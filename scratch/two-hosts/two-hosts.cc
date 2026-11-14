// two-hosts: two nodes on one point-to-point link. Node 0 sends UDP (OnOff) and TCP (BulkSend)
// to node 1 at the same time. A queue disc on node 0's device decides which packet the link carries next.
// Writes <out>/metrics.json, <out>/series.csv and <out>/flowmon.xml. --out must be absolute.
// Traffic runs for warmup + duration seconds; metrics.json covers the last `duration` seconds only.
// series.csv covers the whole run (drops there are totals since the start of traffic).
// With --events=MS, every packet-level event in a window of MS milliseconds is also written to
// <out>/events.csv (time in ns, number of the simulator event it happened in, what, where, flow, packet key).

#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/traffic-control-module.h"

#include "link-queue-disc.h"

#include <filesystem>
#include <fstream>
#include <iomanip>

using namespace ns3;

static uint64_t g_udpTxPkts = 0;
static uint64_t g_udpRxPkts = 0;
// udp_loss_frac counts the UDP packets SENT inside the measured seconds, and how many of exactly those arrived
// (whenever they arrived), so a packet sent just before the measured seconds and received inside them is not counted.
static int64_t g_winFrom = 0; // the measured seconds, in ns
static int64_t g_winTo = 0;
static uint64_t g_udpTxWin = 0;  // UDP packets sent inside them
static uint64_t g_udpRxWin = 0;  // of those, the ones that arrived
static uint64_t g_uidFirst = 0;  // uid of the first and of the last UDP packet sent inside them
static uint64_t g_uidLast = 0;
static uint64_t g_linkTxBytes = 0;
static uint32_t g_cwnd = 0;
static uint64_t g_tcpRetrans = 0;
static uint32_t g_qMin[2] = {0, 0}; // lowest occupancy of each band since the last sample

static std::ofstream g_ev; // events.csv
static int64_t g_evFrom = 0;
static int64_t g_evTo = -1; // window in ns; nothing is recorded while g_evTo < now
static Ptr<QueueDisc> g_band[2];

// One row per thing that happens to a packet inside the window. Rows with the same `ev` happened inside the
// same simulator event (their order within it is the order the code ran, not cause before effect).
// `key` names the packet through its whole life: u<uid> a UDP packet, t<sequence number> a TCP data segment
// (segments cut from one application write have the same uid, so the uid cannot be used), a<uid> a pure TCP ACK.
static void
Ev(const char* kind, const char* obj, const char* flow, char tag, uint64_t id, uint32_t size, int64_t info)
{
    int64_t t = Simulator::Now().GetNanoSeconds();
    if (t < g_evFrom || t > g_evTo)
    {
        return;
    }
    g_ev << t << ',' << Simulator::GetEventCount() << ',' << kind << ',' << obj << ',' << flow << ',' << tag << id << ','
         << size << ',' << info << '\n';
}

// Flow and key of a packet that starts with its transport header (in a queue disc) or with the link header (on a device).
static void
EvPacket(const char* kind, const char* obj, Ptr<const Packet> pkt, bool linkHeader, bool udp, int64_t info)
{
    int64_t t = Simulator::Now().GetNanoSeconds();
    if (t < g_evFrom || t > g_evTo)
    {
        return;
    }
    Ptr<Packet> p = pkt->Copy();
    if (linkHeader)
    {
        PppHeader ppp;
        p->RemoveHeader(ppp);
        Ipv4Header ip;
        p->RemoveHeader(ip);
        udp = ip.GetProtocol() == 17;
    }
    if (udp)
    {
        Ev(kind, obj, "udp", 'u', pkt->GetUid(), pkt->GetSize(), info);
        return;
    }
    TcpHeader tcp;
    p->RemoveHeader(tcp);
    if (p->GetSize() > 0)
    {
        Ev(kind, obj, "tcp", 't', tcp.GetSequenceNumber().GetValue(), pkt->GetSize(), info);
    }
    else
    {
        Ev(kind, obj, "ack", 'a', pkt->GetUid(), pkt->GetSize(), info);
    }
}

static bool
IsUdp(Ptr<const QueueDiscItem> item)
{
    Ptr<const Ipv4QueueDiscItem> ip = DynamicCast<const Ipv4QueueDiscItem>(item);
    return ip && ip->GetHeader().GetProtocol() == 17;
}
static void QEnqueue(uint32_t band, Ptr<const QueueDiscItem> item)
{
    EvPacket("enqueue", band ? "queue1" : "queue0", item->GetPacket(), false, IsUdp(item), g_band[band]->GetNPackets());
}
static void QDequeue(uint32_t band, Ptr<const QueueDiscItem> item)
{
    EvPacket("dequeue", band ? "queue1" : "queue0", item->GetPacket(), false, IsUdp(item), g_band[band]->GetNPackets());
}
static void QDrop(uint32_t band, Ptr<const QueueDiscItem> item)
{
    EvPacket("drop", band ? "queue1" : "queue0", item->GetPacket(), false, IsUdp(item), g_band[band]->GetNPackets());
}
static void DevTxBegin(uint32_t dev, Ptr<const Packet> p) { EvPacket("tx_begin", dev ? "dev1" : "dev0", p, true, false, 0); }
static void DevTxEnd(uint32_t dev, Ptr<const Packet> p) { EvPacket("tx_end", dev ? "dev1" : "dev0", p, true, false, 0); }
static void DevRx(uint32_t dev, Ptr<const Packet> p) { EvPacket("rx", dev ? "dev1" : "dev0", p, true, false, 0); }
static void TcpTxEv(std::string ctx, Ptr<const Packet> p, const TcpHeader& h, Ptr<const TcpSocketBase>)
{
    bool sender = ctx.rfind("/NodeList/0/", 0) == 0;
    if (p->GetSize() > 0)
    {
        Ev("tcp_send", sender ? "tcp0" : "tcp1", "tcp", 't', h.GetSequenceNumber().GetValue(), p->GetSize(), h.GetSequenceNumber().GetValue());
    }
    else
    {
        Ev("ack_send", sender ? "tcp0" : "tcp1", "ack", 'a', p->GetUid(), p->GetSize(), h.GetAckNumber().GetValue());
    }
}
static void TcpRxEv(std::string ctx, Ptr<const Packet> p, const TcpHeader& h, Ptr<const TcpSocketBase>)
{
    bool sender = ctx.rfind("/NodeList/0/", 0) == 0;
    if (p->GetSize() > 0)
    {
        Ev("tcp_rx", sender ? "tcp0" : "tcp1", "tcp", 't', h.GetSequenceNumber().GetValue(), p->GetSize(), h.GetSequenceNumber().GetValue());
    }
    else
    {
        Ev("ack_rx", sender ? "tcp0" : "tcp1", "ack", 'a', p->GetUid(), p->GetSize(), h.GetAckNumber().GetValue());
    }
}

static void UdpTx(Ptr<const Packet> p)
{
    ++g_udpTxPkts;
    int64_t now = Simulator::Now().GetNanoSeconds();
    if (now >= g_winFrom && now < g_winTo)
    {
        if (g_udpTxWin == 0)
        {
            g_uidFirst = p->GetUid();
        }
        g_uidLast = p->GetUid();
        ++g_udpTxWin;
    }
    Ev("create", "udp0", "udp", 'u', p->GetUid(), p->GetSize(), 0);
}
static void UdpRx(Ptr<const Packet> p, const Address&)
{
    ++g_udpRxPkts;
    if (g_udpTxWin > 0 && p->GetUid() >= g_uidFirst && p->GetUid() <= g_uidLast)
    {
        ++g_udpRxWin;
    }
    Ev("deliver", "udp1", "udp", 'u', p->GetUid(), p->GetSize(), 0);
}
static void LinkTx(Ptr<const Packet> p) { g_linkTxBytes += p->GetSize(); }
static void CwndChange(uint32_t, uint32_t now)
{
    g_cwnd = now;
    Ev("cwnd", "tcp0", "tcp", 'w', 0, 0, now);
}
static void Retrans(Ptr<const Packet> p, const TcpHeader& h, const Address&, const Address&, Ptr<const TcpSocketBase>)
{
    ++g_tcpRetrans;
    Ev("retransmit", "tcp0", "tcp", 't', h.GetSequenceNumber().GetValue(), p->GetSize(), h.GetSequenceNumber().GetValue());
}
static void Q0(uint32_t, uint32_t now) { g_qMin[0] = std::min(g_qMin[0], now); }
static void Q1(uint32_t, uint32_t now) { g_qMin[1] = std::min(g_qMin[1], now); }

// Counter values at one instant; metrics are the difference between two of these.
struct Counters
{
    uint64_t udpRxBytes = 0;
    uint64_t tcpRxBytes = 0;
    uint64_t udpTxPkts = 0;
    uint64_t udpRxPkts = 0;
    uint64_t linkTxBytes = 0;
    uint64_t tcpRetrans = 0;
    uint32_t drops[2] = {0, 0};
};

struct Sampler
{
    Ptr<PacketSink> udpSink;
    Ptr<PacketSink> tcpSink;
    Ptr<QueueDisc> root;
    std::ofstream csv;
    uint64_t lastUdp = 0;
    uint64_t lastTcp = 0;
    double period = 0.1;
    double tStop = 0;

    void Sample()
    {
        uint64_t u = udpSink->GetTotalRx();
        uint64_t t = tcpSink->GetTotalRx();
        csv << std::fixed << std::setprecision(3) << Simulator::Now().GetSeconds() << ","
            << std::setprecision(0) << (u - lastUdp) * 8.0 / period << "," << (t - lastTcp) * 8.0 / period
            << "," << g_cwnd << "," << Drops(0) << "," << Drops(1) << "," << Occupancy(0) << "," << Occupancy(1)
            << "," << g_qMin[0] << "," << g_qMin[1] << "\n";
        g_qMin[0] = Occupancy(0);
        g_qMin[1] = Occupancy(1);
        lastUdp = u;
        lastTcp = t;
        if (Simulator::Now().GetSeconds() + period <= tStop + 1e-9)
        {
            Simulator::Schedule(Seconds(period), &Sampler::Sample, this);
        }
    }

    uint32_t Drops(std::size_t band) const
    {
        return root->GetQueueDiscClass(band)->GetQueueDisc()->GetStats().nTotalDroppedPackets;
    }

    uint32_t Occupancy(std::size_t band) const
    {
        return root->GetQueueDiscClass(band)->GetQueueDisc()->GetNPackets();
    }

    void Take(Counters* c) const
    {
        c->udpRxBytes = udpSink->GetTotalRx();
        c->tcpRxBytes = tcpSink->GetTotalRx();
        c->udpTxPkts = g_udpTxPkts;
        c->udpRxPkts = g_udpRxPkts;
        c->linkTxBytes = g_linkTxBytes;
        c->tcpRetrans = g_tcpRetrans;
        c->drops[0] = Drops(0);
        c->drops[1] = Drops(1);
    }
};

int
main(int argc, char* argv[])
{
    std::string linkRate = "1Gbps";
    std::string linkDelay = "50us";
    std::string udpRate = "2Gbps";
    std::string tcpVariant = "TcpCubic";
    uint32_t mtu = 1500;
    uint32_t queuePkts = 100;
    uint32_t queuePktsUdp = 0; // 0: the UDP queue is as long as queuePkts says
    uint32_t queuePktsTcp = 0; // 0: the TCP queue is as long as queuePkts says
    double duration = 10;
    uint32_t seed = 1;
    double weightUdp = 0.5;
    std::string out;
    bool pcap = false;
    double warmup = 1.0;
    bool tcpOn = true;
    uint32_t udpTos = 0x10;
    double events = 0;
    double eventsAt = 0;

    CommandLine cmd(__FILE__);
    cmd.AddValue("linkRate", "Link rate", linkRate);
    cmd.AddValue("linkDelay", "One-way link delay", linkDelay);
    cmd.AddValue("udpRate", "UDP sending rate", udpRate);
    cmd.AddValue("tcpVariant", "TCP congestion control (ns-3 type name without ns3::)", tcpVariant);
    cmd.AddValue("mtu", "Link MTU in bytes", mtu);
    cmd.AddValue("queuePkts", "Queue length per band in packets", queuePkts);
    cmd.AddValue("queuePktsUdp", "Length of the UDP queue alone, in packets (0 = queuePkts)", queuePktsUdp);
    cmd.AddValue("queuePktsTcp", "Length of the TCP queue alone, in packets (0 = queuePkts)", queuePktsTcp);
    cmd.AddValue("duration", "Seconds of traffic", duration);
    cmd.AddValue("seed", "Random run number", seed);
    cmd.AddValue("weightUdp", "Part of the link configured for UDP, 0.05-0.95", weightUdp);
    cmd.AddValue("out", "Absolute output directory", out);
    cmd.AddValue("pcap", "Write pcap traces", pcap);
    cmd.AddValue("warmup", "Seconds of traffic before the measured window", warmup);
    cmd.AddValue("tcp", "Run the TCP sender", tcpOn);
    cmd.AddValue("udpTos", "TOS byte of the UDP sender", udpTos);
    cmd.AddValue("events", "Milliseconds of packet-level events to write to events.csv (0 = none)", events);
    cmd.AddValue("eventsAt", "Start of that window in seconds (0 = half a second into the measured time)", eventsAt);
    cmd.Parse(argc, argv);

    if (out.empty() || out[0] != '/')
    {
        std::cerr << "--out must be an absolute path\n";
        return 1;
    }
    std::filesystem::create_directories(out);

    RngSeedManager::SetSeed(1);
    RngSeedManager::SetRun(seed);
    Config::SetDefault("ns3::TcpL4Protocol::SocketType",
                       TypeIdValue(TypeId::LookupByName("ns3::" + tcpVariant)));
    // 20 IP + 20 TCP + 12 timestamp option: a full segment is exactly one MTU-sized packet
    Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(mtu - 52));
    Config::SetDefault("ns3::TcpSocket::SndBufSize", UintegerValue(1 << 20));
    Config::SetDefault("ns3::TcpSocket::RcvBufSize", UintegerValue(1 << 20));

    NodeContainer nodes;
    nodes.Create(2);

    PointToPointHelper p2p;
    p2p.SetDeviceAttribute("DataRate", StringValue(linkRate));
    p2p.SetDeviceAttribute("Mtu", UintegerValue(mtu));
    p2p.SetChannelAttribute("Delay", StringValue(linkDelay));
    p2p.SetQueue("ns3::DropTailQueue<Packet>", "MaxSize", StringValue("10p"));
    NetDeviceContainer devs = p2p.Install(nodes);

    InternetStackHelper stack;
    stack.Install(nodes);

    // Scheduler on the sending device: two bands, UDP (socket priority 6) in band 0, TCP in band 1.
    TrafficControlHelper tch;
    uint16_t h = tch.SetRootQueueDisc("ns3::LinkQueueDisc", "WeightUdp", DoubleValue(weightUdp));
    TrafficControlHelper::ClassIdList cids = tch.AddQueueDiscClasses(h, 2, "ns3::QueueDiscClass");
    // Each queue has the common length unless its own length is given.
    std::string qsizeUdp = std::to_string(queuePktsUdp ? queuePktsUdp : queuePkts) + "p";
    std::string qsizeTcp = std::to_string(queuePktsTcp ? queuePktsTcp : queuePkts) + "p";
    tch.AddChildQueueDisc(h, cids[0], "ns3::FifoQueueDisc", "MaxSize", StringValue(qsizeUdp));
    tch.AddChildQueueDisc(h, cids[1], "ns3::FifoQueueDisc", "MaxSize", StringValue(qsizeTcp));
    QueueDiscContainer qdiscs = tch.Install(devs.Get(0));

    Ipv4AddressHelper addr;
    addr.SetBase("10.0.0.0", "255.255.255.0");
    Ipv4InterfaceContainer ifs = addr.Assign(devs);
    Ipv4Address dst = ifs.GetAddress(1);

    const double tStart = 1.0;
    const double tMeasure = tStart + warmup;
    const double tStop = tMeasure + duration;
    g_winFrom = Seconds(tMeasure).GetNanoSeconds();
    g_winTo = Seconds(tStop).GetNanoSeconds();
    // Each sender starts up to 10 ms after tStart; the offsets depend on --seed.
    Ptr<UniformRandomVariable> offset = CreateObject<UniformRandomVariable>();
    const double udpAt = tStart + offset->GetValue(0.0, 0.01);
    const double tcpAt = tStart + offset->GetValue(0.0, 0.01);
    const bool udpOn = DataRate(udpRate).GetBitRate() > 0;

    ApplicationContainer udpApp;
    if (udpOn)
    {
        OnOffHelper udp("ns3::UdpSocketFactory", InetSocketAddress(dst, 9));
        udp.SetConstantRate(DataRate(udpRate), 1400);
        udp.SetAttribute("Tos", UintegerValue(udpTos));
        udpApp = udp.Install(nodes.Get(0));
        udpApp.Start(Seconds(udpAt));
        udpApp.Stop(Seconds(tStop));
    }

    if (tcpOn)
    {
        BulkSendHelper tcp("ns3::TcpSocketFactory", InetSocketAddress(dst, 10));
        tcp.SetAttribute("MaxBytes", UintegerValue(0));
        tcp.SetAttribute("Tos", UintegerValue(0));
        ApplicationContainer tcpApp = tcp.Install(nodes.Get(0));
        tcpApp.Start(Seconds(tcpAt));
        tcpApp.Stop(Seconds(tStop));
    }

    PacketSinkHelper udpSinkH("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), 9));
    PacketSinkHelper tcpSinkH("ns3::TcpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), 10));
    ApplicationContainer sinks = udpSinkH.Install(nodes.Get(1));
    sinks.Add(tcpSinkH.Install(nodes.Get(1)));
    sinks.Start(Seconds(0.0));
    sinks.Stop(Seconds(tStop + 1.0));

    if (udpOn)
    {
        udpApp.Get(0)->TraceConnectWithoutContext("Tx", MakeCallback(&UdpTx));
    }
    sinks.Get(0)->TraceConnectWithoutContext("Rx", MakeCallback(&UdpRx));
    devs.Get(0)->TraceConnectWithoutContext("PhyTxEnd", MakeCallback(&LinkTx));
    Simulator::Schedule(Seconds(tcpAt) + MicroSeconds(1), [] {
        Config::ConnectWithoutContextFailSafe("/NodeList/0/$ns3::TcpL4Protocol/SocketList/*/CongestionWindow",
                                              MakeCallback(&CwndChange));
        Config::ConnectWithoutContextFailSafe("/NodeList/0/$ns3::TcpL4Protocol/SocketList/*/Retransmission",
                                              MakeCallback(&Retrans));
    });
    qdiscs.Get(0)->GetQueueDiscClass(0)->GetQueueDisc()->TraceConnectWithoutContext("PacketsInQueue", MakeCallback(&Q0));
    qdiscs.Get(0)->GetQueueDiscClass(1)->GetQueueDisc()->TraceConnectWithoutContext("PacketsInQueue", MakeCallback(&Q1));

    if (events > 0)
    {
        const double evAt = eventsAt > 0 ? eventsAt : tMeasure + 0.5;
        g_evFrom = Seconds(evAt).GetNanoSeconds();
        g_evTo = g_evFrom + MilliSeconds(1).GetNanoSeconds() * events;
        g_ev.open(out + "/events.csv");
        g_ev << "t_ns,ev,kind,obj,flow,key,size,info\n";
        for (uint32_t b = 0; b < 2; b++)
        {
            g_band[b] = qdiscs.Get(0)->GetQueueDiscClass(b)->GetQueueDisc();
            g_band[b]->TraceConnectWithoutContext("Enqueue", MakeBoundCallback(&QEnqueue, b));
            g_band[b]->TraceConnectWithoutContext("Dequeue", MakeBoundCallback(&QDequeue, b));
            g_band[b]->TraceConnectWithoutContext("Drop", MakeBoundCallback(&QDrop, b));
        }
        for (uint32_t d = 0; d < 2; d++)
        {
            devs.Get(d)->TraceConnectWithoutContext("PhyTxBegin", MakeBoundCallback(&DevTxBegin, d));
            devs.Get(d)->TraceConnectWithoutContext("PhyTxEnd", MakeBoundCallback(&DevTxEnd, d));
            devs.Get(d)->TraceConnectWithoutContext("PhyRxEnd", MakeBoundCallback(&DevRx, d));
        }
        // the sockets of both ends exist by now; packets are followed from just before the window
        Simulator::Schedule(Seconds(evAt) - MilliSeconds(1), [] {
            Config::ConnectFailSafe("/NodeList/*/$ns3::TcpL4Protocol/SocketList/*/Tx", MakeCallback(&TcpTxEv));
            Config::ConnectFailSafe("/NodeList/*/$ns3::TcpL4Protocol/SocketList/*/Rx", MakeCallback(&TcpRxEv));
        });
    }

    Sampler sampler;
    sampler.udpSink = DynamicCast<PacketSink>(sinks.Get(0));
    sampler.tcpSink = DynamicCast<PacketSink>(sinks.Get(1));
    sampler.root = qdiscs.Get(0);
    sampler.tStop = tStop;
    sampler.csv.open(out + "/series.csv");
    sampler.csv << "t,udp_bps,tcp_bps,cwnd,drops_band0,drops_band1,q_band0,q_band1,qmin_band0,qmin_band1\n";
    Simulator::Schedule(Seconds(tStart + sampler.period), &Sampler::Sample, &sampler);
    Counters c0;
    Counters c1;
    Simulator::Schedule(Seconds(tMeasure), &Sampler::Take, &sampler, &c0);
    Simulator::Schedule(Seconds(tStop), &Sampler::Take, &sampler, &c1);

    if (pcap)
    {
        p2p.EnablePcapAll(out + "/two-hosts");
    }
    FlowMonitorHelper fmh;
    Ptr<FlowMonitor> fm = fmh.InstallAll();

    Simulator::Stop(Seconds(tStop + 1.0));
    Simulator::Run();

    uint64_t linkBps = DataRate(linkRate).GetBitRate();
    double udpBps = (c1.udpRxBytes - c0.udpRxBytes) * 8.0 / duration;
    double tcpBps = (c1.tcpRxBytes - c0.tcpRxBytes) * 8.0 / duration;
    double loss = g_udpTxWin ? 1.0 - double(g_udpRxWin) / double(g_udpTxWin) : 0.0;
    double util = (c1.linkTxBytes - c0.linkTxBytes) * 8.0 / duration / double(linkBps);

    std::ofstream pj(out + "/params.json");
    pj << "{\"linkRate\": \"" << linkRate << "\", \"linkDelay\": \"" << linkDelay << "\", \"udpRate\": \"" << udpRate
       << "\", \"tcpVariant\": \"" << tcpVariant << "\", \"mtu\": " << mtu << ", \"queuePkts\": " << queuePkts
       << ", \"duration\": " << duration << ", \"seed\": " << seed << ", \"weightUdp\": " << weightUdp;
    // A setting added after build 4 is stated only when it was given, so a run without it writes the file it always wrote.
    if (queuePktsUdp)
    {
        pj << ", \"queuePktsUdp\": " << queuePktsUdp;
    }
    if (queuePktsTcp)
    {
        pj << ", \"queuePktsTcp\": " << queuePktsTcp;
    }
    pj << "}\n";
    pj.close();
    std::ofstream m(out + "/metrics.json");
    m << std::fixed << std::setprecision(0) << "{\n"
      << "  \"udp_goodput_bps\": " << udpBps << ",\n"
      << "  \"tcp_goodput_bps\": " << tcpBps << ",\n"
      << std::setprecision(6) << "  \"udp_loss_frac\": " << loss << ",\n"
      << "  \"drops_band0\": " << c1.drops[0] - c0.drops[0] << ",\n"
      << "  \"drops_band1\": " << c1.drops[1] - c0.drops[1] << ",\n"
      << "  \"tcp_retrans\": " << c1.tcpRetrans - c0.tcpRetrans << ",\n"
      << "  \"link_util\": " << util << ",\n"
      << "  \"link_rate_bps\": " << linkBps << ",\n"
      << "  \"weight_udp\": " << weightUdp << "\n"
      << "}\n";
    m.close();
    fm->SerializeToXmlFile(out + "/flowmon.xml", false, false);
    sampler.csv.close();
    if (g_ev.is_open())
    {
        g_ev.close();
    }
    Simulator::Destroy();
    return 0;
}
