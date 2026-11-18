// net: a network built from a description. Hosts joined by point-to-point links, UDP and TCP flows between them,
// a plain queue or the scheduler (FlowQueueDisc) on the sending side of a link.
//
//   net --net=/abs/network.txt --out=/abs/dir
//
// network.txt, one object per line (words, then name=value pairs; a line that starts with # is skipped):
//   host  <id>
//   link  <id> <host> <host> rate=1Gbps delay=50us mtu=1500 devq=10
//   dev   <link> <host> [rate=1Gbps] [devq=10]   the device of that host on that link, where it differs from the link's line
//   queue <link> <host> kind=fifo|scheduler length=100 [parts=<name>:<part>,...] [largest=<name>:<rate>,...] [classes=<name>:<flow>+<flow>,...]
//         a part's name is a flow (that flow has a queue of its own), or a class: several flows that share one queue of the scheduler
//   flow  <id> udp <from> <to> rate=2Gbps packet=1400
//   flow  <id> tcp <from> <to> type=TcpCubic [app=onoff rate=200Mbps packet=1400]
//         udp or tcp is the socket the application opens (ns-3: its Protocol, a socket factory). app is the ns-3 application
//         that sends: onoff (OnOffApplication, always on: packets at a constant rate) or bulk (BulkSendApplication: as fast
//         as the socket accepts; it needs a TCP socket). Left out, a udp flow is onoff and a tcp flow is bulk.
//   tcp   [initcwnd=10] [buf=1048576]          for every TCP flow
//   run   duration=10 seed=1 [warmup=1]
// A link has a queue on each of its two sending sides. A side a `queue` line names gets that queue (both sides may be
// named); every other side gets a plain queue of 100 packets. A host with more than one link forwards.
// How a scheduler divides the link is not in the description: it is the environment variable TWOHOSTS_SCHED.
//
// Written to --out: metrics.json (the measured seconds) and series.csv (a sample every 0.1 s), with these names:
//   <flow>_goodput_bps            payload bits per second delivered to the flow's receiver
//   <flow>_loss_frac              UDP: part of the packets sent in the measured seconds that never arrived
//   <flow>_retrans                TCP: segments the sender sent again
//   <link>_util, <link>_util_back bits sent on the wire divided by the link's rate, first host to second, and back
//   <link>_drops_<flow>           packets dropped from that flow's band of the link's scheduler
//   <link>_drops                  packets dropped from the link's plain queue (when its queue is a plain one)
//   <link>_drops_back             packets dropped from the plain queue of the link's other side
#include "flow-queue-disc.h"

#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/traffic-control-module.h"

#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

using namespace ns3;

struct FlowState
{
    std::string id;
    bool udp = false;   // the socket: UDP, else TCP
    bool onoff = false; // the application: OnOffApplication (a constant rate), else BulkSendApplication
    std::string from, to, type = "TcpCubic";
    std::string rate = "0bps";
    uint32_t packet = 1400;
    uint16_t port = 0;
    double startAt = 0;
    Ptr<PacketSink> sink;
    Ptr<Application> app;
    // counters
    uint64_t txWin = 0, rxWin = 0, uidFirst = 0, uidLast = 0, retrans = 0;
    uint32_t cwnd = 0;
    uint64_t lastRx = 0, rx0 = 0, rx1 = 0, retrans0 = 0, retrans1 = 0;
};

struct QueueSpec
{
    bool given = false;
    std::string kind = "fifo";
    uint32_t length = 100;
    std::vector<std::pair<std::string, double>> parts;
    std::map<std::string, std::string> largest;
    std::map<std::string, std::vector<std::string>> classes; // a part's name -> the flows that share its queue (absent: the name is one flow)
};

struct LinkState
{
    std::string id, a, b, rate = "1Gbps", delay = "50us";
    uint32_t mtu = 1500, devq = 10;
    std::string rateOf[2];        // the rate of the device of a, of b, where a `dev` line gives one (empty: the link's)
    uint32_t devqOf[2] = {0, 0}; // its transmit queue, in packets (0: the link's)
    QueueSpec q[2]; // on the side of a, on the side of b
    NetDeviceContainer devs;
    Ptr<QueueDisc> root[2];
    uint64_t tx[2] = {0, 0}, tx0[2] = {0, 0}, tx1[2] = {0, 0};
    std::vector<uint32_t> drops0[2], drops1[2];
};

static int64_t g_winFrom = 0;
static int64_t g_winTo = 0;

static void
UdpTx(FlowState* f, Ptr<const Packet> p)
{
    int64_t now = Simulator::Now().GetNanoSeconds();
    if (now >= g_winFrom && now < g_winTo)
    {
        if (f->txWin == 0)
        {
            f->uidFirst = p->GetUid();
        }
        f->uidLast = p->GetUid();
        ++f->txWin;
    }
}
static void
UdpRx(FlowState* f, Ptr<const Packet> p, const Address&)
{
    if (f->txWin > 0 && p->GetUid() >= f->uidFirst && p->GetUid() <= f->uidLast)
    {
        ++f->rxWin;
    }
}
static void
Cwnd(FlowState* f, uint32_t, uint32_t now)
{
    f->cwnd = now;
}
static void
Retrans(FlowState* f, Ptr<const Packet>, const TcpHeader&, const Address&, const Address&, Ptr<const TcpSocketBase>)
{
    ++f->retrans;
}
static void
LinkTx(LinkState* l, uint32_t side, Ptr<const Packet> p)
{
    l->tx[side] += p->GetSize();
}

static std::map<std::string, std::string>
Pairs(std::istringstream& in)
{
    std::map<std::string, std::string> m;
    std::string tok;
    while (in >> tok)
    {
        auto eq = tok.find('=');
        NS_ABORT_MSG_IF(eq == std::string::npos, "expected name=value, got '" << tok << "'");
        m[tok.substr(0, eq)] = tok.substr(eq + 1);
    }
    return m;
}
static std::vector<std::pair<std::string, std::string>>
List(const std::string& s)
{
    std::vector<std::pair<std::string, std::string>> v;
    std::istringstream in(s);
    std::string item;
    while (std::getline(in, item, ','))
    {
        auto c = item.find(':');
        NS_ABORT_MSG_IF(c == std::string::npos, "expected name:value, got '" << item << "'");
        v.emplace_back(item.substr(0, c), item.substr(c + 1));
    }
    return v;
}

static std::vector<uint32_t>
Drops(Ptr<QueueDisc> root)
{
    std::vector<uint32_t> d;
    if (root->GetNQueueDiscClasses() == 0)
    {
        d.push_back(root->GetStats().nTotalDroppedPackets);
        return d;
    }
    for (uint32_t i = 0; i < root->GetNQueueDiscClasses(); i++)
    {
        d.push_back(root->GetQueueDiscClass(i)->GetQueueDisc()->GetStats().nTotalDroppedPackets);
    }
    return d;
}

int
main(int argc, char* argv[])
{
    std::string netFile;
    std::string out;
    CommandLine cmd(__FILE__);
    cmd.AddValue("net", "Absolute path of the network description", netFile);
    cmd.AddValue("out", "Absolute output directory", out);
    cmd.Parse(argc, argv);
    if (out.empty() || out[0] != '/' || netFile.empty() || netFile[0] != '/')
    {
        std::cerr << "--net and --out must be absolute paths\n";
        return 1;
    }
    std::filesystem::create_directories(out);

    // ---- read the description
    std::vector<std::string> hosts;
    std::vector<LinkState> links;
    std::vector<FlowState> flows;
    double duration = 10, warmup = 1;
    uint32_t seed = 1, initCwnd = 0, bufBytes = 0;
    std::ifstream in(netFile);
    NS_ABORT_MSG_IF(!in, "cannot read " << netFile);
    std::string line;
    auto linkOf = [&](const std::string& id) -> LinkState& {
        for (auto& l : links)
        {
            if (l.id == id)
            {
                return l;
            }
        }
        NS_ABORT_MSG("no link '" << id << "'");
    };
    auto hostOf = [&](const std::string& id) -> uint32_t {
        for (uint32_t i = 0; i < hosts.size(); i++)
        {
            if (hosts[i] == id)
            {
                return i;
            }
        }
        NS_ABORT_MSG("no host '" << id << "'");
    };
    while (std::getline(in, line))
    {
        std::istringstream ls(line);
        std::string what;
        if (!(ls >> what) || what[0] == '#')
        {
            continue;
        }
        if (what == "host")
        {
            std::string id;
            ls >> id;
            hosts.push_back(id);
        }
        else if (what == "link")
        {
            LinkState l;
            ls >> l.id >> l.a >> l.b;
            auto m = Pairs(ls);
            l.rate = m.count("rate") ? m["rate"] : l.rate;
            l.delay = m.count("delay") ? m["delay"] : l.delay;
            l.mtu = m.count("mtu") ? std::stoul(m["mtu"]) : l.mtu;
            l.devq = m.count("devq") ? std::stoul(m["devq"]) : l.devq;
            links.push_back(l);
        }
        else if (what == "dev")
        {
            std::string lid, host;
            ls >> lid >> host;
            LinkState& l = linkOf(lid);
            NS_ABORT_MSG_IF(host != l.a && host != l.b, "dev: host '" << host << "' is not on link '" << lid << "'");
            uint32_t side = host == l.a ? 0 : 1;
            auto m = Pairs(ls);
            l.rateOf[side] = m.count("rate") ? m["rate"] : l.rateOf[side];
            l.devqOf[side] = m.count("devq") ? std::stoul(m["devq"]) : l.devqOf[side];
        }
        else if (what == "queue")
        {
            std::string lid, host;
            ls >> lid >> host;
            LinkState& l = linkOf(lid);
            NS_ABORT_MSG_IF(host != l.a && host != l.b, "queue: host '" << host << "' is not on link '" << lid << "'");
            QueueSpec& q = l.q[host == l.a ? 0 : 1];
            auto m = Pairs(ls);
            q.given = true;
            q.kind = m.count("kind") ? m["kind"] : "fifo";
            q.length = m.count("length") ? std::stoul(m["length"]) : 100;
            if (m.count("parts"))
            {
                for (auto& [k, v] : List(m["parts"]))
                {
                    q.parts.emplace_back(k, std::stod(v));
                }
            }
            if (m.count("largest"))
            {
                for (auto& [k, v] : List(m["largest"]))
                {
                    q.largest[k] = v;
                }
            }
            if (m.count("classes"))
            {
                for (auto& [k, v] : List(m["classes"]))
                {
                    std::stringstream fs(v);
                    std::string f;
                    while (std::getline(fs, f, '+'))
                    {
                        q.classes[k].push_back(f);
                    }
                }
            }
            NS_ABORT_MSG_IF(q.kind != "fifo" && q.kind != "scheduler", "queue kind must be fifo or scheduler");
            NS_ABORT_MSG_IF(q.kind == "scheduler" && q.parts.empty(), "a scheduler needs parts");
        }
        else if (what == "flow")
        {
            FlowState f;
            std::string kind;
            ls >> f.id >> kind >> f.from >> f.to;
            NS_ABORT_MSG_IF(kind != "udp" && kind != "tcp", "flow kind must be udp or tcp");
            f.udp = kind == "udp";
            auto m = Pairs(ls);
            f.rate = m.count("rate") ? m["rate"] : f.rate;
            f.packet = m.count("packet") ? std::stoul(m["packet"]) : f.packet;
            f.type = m.count("type") ? m["type"] : f.type;
            std::string app = m.count("app") ? m["app"] : (f.udp ? "onoff" : "bulk");
            NS_ABORT_MSG_IF(app != "onoff" && app != "bulk", "flow app must be onoff or bulk");
            NS_ABORT_MSG_IF(app == "bulk" && f.udp, "flow '" << f.id << "': BulkSendApplication needs a TCP socket");
            f.onoff = app == "onoff";
            f.port = 9000 + flows.size();
            flows.push_back(f);
        }
        else if (what == "tcp")
        {
            auto m = Pairs(ls);
            initCwnd = m.count("initcwnd") ? std::stoul(m["initcwnd"]) : 0;
            bufBytes = m.count("buf") ? std::stoul(m["buf"]) : 0;
        }
        else if (what == "run")
        {
            auto m = Pairs(ls);
            duration = m.count("duration") ? std::stod(m["duration"]) : duration;
            seed = m.count("seed") ? std::stoul(m["seed"]) : seed;
            warmup = m.count("warmup") ? std::stod(m["warmup"]) : warmup;
        }
        else
        {
            NS_ABORT_MSG("unknown line '" << what << "'");
        }
    }
    NS_ABORT_MSG_IF(hosts.size() < 2 || links.empty(), "a network needs at least two hosts and one link");

    RngSeedManager::SetSeed(1);
    RngSeedManager::SetRun(seed);
    uint32_t minMtu = links[0].mtu;
    for (auto& l : links)
    {
        minMtu = std::min(minMtu, l.mtu);
    }
    // 20 IP + 20 TCP + 12 timestamp option: a full segment is one packet of the smallest MTU on the way
    Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(minMtu - 52));
    Config::SetDefault("ns3::TcpSocket::SndBufSize", UintegerValue(bufBytes ? bufBytes : (1 << 20)));
    Config::SetDefault("ns3::TcpSocket::RcvBufSize", UintegerValue(bufBytes ? bufBytes : (1 << 20)));
    if (initCwnd)
    {
        Config::SetDefault("ns3::TcpSocket::InitialCwnd", UintegerValue(initCwnd));
    }

    // ---- hosts and links
    NodeContainer nodes;
    nodes.Create(hosts.size());
    InternetStackHelper stack;
    stack.Install(nodes);
    std::vector<Ipv4Address> addrOf(hosts.size()); // a host's address on its first link
    std::vector<bool> has(hosts.size(), false);
    std::map<std::string, uint16_t> portOf;
    for (auto& f : flows)
    {
        portOf[f.id] = f.port;
    }
    for (uint32_t k = 0; k < links.size(); k++)
    {
        LinkState& l = links[k];
        uint32_t ia = hostOf(l.a), ib = hostOf(l.b);
        PointToPointHelper p2p;
        p2p.SetDeviceAttribute("DataRate", StringValue(l.rate));
        p2p.SetDeviceAttribute("Mtu", UintegerValue(l.mtu));
        p2p.SetChannelAttribute("Delay", StringValue(l.delay));
        p2p.SetQueue("ns3::DropTailQueue<Packet>", "MaxSize", StringValue(std::to_string(l.devq) + "p"));
        l.devs = p2p.Install(nodes.Get(ia), nodes.Get(ib));
        for (uint32_t side = 0; side < 2; side++) // a device that differs from its link's line: its own rate, its own transmit queue
        {
            if (!l.rateOf[side].empty())
            {
                l.devs.Get(side)->SetAttribute("DataRate", StringValue(l.rateOf[side]));
            }
            if (l.devqOf[side])
            {
                DynamicCast<PointToPointNetDevice>(l.devs.Get(side))->GetQueue()->SetAttribute("MaxSize", StringValue(std::to_string(l.devqOf[side]) + "p"));
            }
        }
        for (uint32_t side = 0; side < 2; side++)
        {
            const QueueSpec& q = l.q[side];
            TrafficControlHelper tch;
            std::string size = std::to_string(q.length) + "p";
            if (q.kind == "scheduler")
            {
                uint16_t h = tch.SetRootQueueDisc("ns3::FlowQueueDisc");
                TrafficControlHelper::ClassIdList cids = tch.AddQueueDiscClasses(h, q.parts.size() + 1, "ns3::QueueDiscClass");
                for (uint32_t i = 0; i <= q.parts.size(); i++)
                {
                    tch.AddChildQueueDisc(h, cids[i], "ns3::FifoQueueDisc", "MaxSize", StringValue(size));
                }
            }
            else
            {
                tch.SetRootQueueDisc("ns3::FifoQueueDisc", "MaxSize", StringValue(size));
            }
            l.root[side] = tch.Install(l.devs.Get(side)).Get(0);
            if (q.kind == "scheduler")
            {
                std::vector<FlowQueueDisc::Band> bands;
                for (auto& [fid, part] : q.parts)
                {
                    std::vector<uint16_t> ports; // the flows whose packets wait in this queue: the class's, or the one flow the part is named after
                    auto cl = q.classes.find(fid);
                    for (const std::string& f : cl == q.classes.end() ? std::vector<std::string>{fid} : cl->second)
                    {
                        NS_ABORT_MSG_IF(!portOf.count(f), "queue of link '" << l.id << "': no flow '" << f << "'");
                        ports.push_back(portOf[f]);
                    }
                    auto lr = q.largest.find(fid);
                    bands.push_back({ports, part, DataRate(lr == q.largest.end() ? "0bps" : lr->second)});
                }
                DynamicCast<FlowQueueDisc>(l.root[side])->SetBands(bands);
            }
            l.devs.Get(side)->TraceConnectWithoutContext("PhyTxEnd", MakeBoundCallback(&LinkTx, &l, side));
        }
        Ipv4AddressHelper addr;
        std::string base = "10." + std::to_string(1 + k / 250) + "." + std::to_string(1 + k % 250) + ".0";
        addr.SetBase(base.c_str(), "255.255.255.0");
        Ipv4InterfaceContainer ifs = addr.Assign(l.devs);
        if (!has[ia])
        {
            addrOf[ia] = ifs.GetAddress(0);
            has[ia] = true;
        }
        if (!has[ib])
        {
            addrOf[ib] = ifs.GetAddress(1);
            has[ib] = true;
        }
    }
    Ipv4GlobalRoutingHelper::PopulateRoutingTables();

    // ---- flows
    const double tStart = 1.0;
    const double tMeasure = tStart + warmup;
    const double tStop = tMeasure + duration;
    g_winFrom = Seconds(tMeasure).GetNanoSeconds();
    g_winTo = Seconds(tStop).GetNanoSeconds();
    Ptr<UniformRandomVariable> offset = CreateObject<UniformRandomVariable>();
    for (auto& f : flows)
    {
        uint32_t from = hostOf(f.from), to = hostOf(f.to);
        NS_ABORT_MSG_IF(!has[to] || !has[from], "flow '" << f.id << "': a host without a link");
        f.startAt = tStart + offset->GetValue(0.0, 0.01); // each flow starts up to 10 ms after tStart; the offsets depend on the seed
        InetSocketAddress dst(addrOf[to], f.port);
        const char* factory = f.udp ? "ns3::UdpSocketFactory" : "ns3::TcpSocketFactory";
        PacketSinkHelper sinkH(factory, InetSocketAddress(Ipv4Address::GetAny(), f.port));
        ApplicationContainer sink = sinkH.Install(nodes.Get(to));
        sink.Start(Seconds(0.0));
        sink.Stop(Seconds(tStop + 1.0));
        f.sink = DynamicCast<PacketSink>(sink.Get(0));
        if (f.onoff)
        {
            if (DataRate(f.rate).GetBitRate() > 0)
            {
                OnOffHelper onoff(factory, dst);
                onoff.SetConstantRate(DataRate(f.rate), f.packet);
                ApplicationContainer app = onoff.Install(nodes.Get(from));
                app.Start(Seconds(f.startAt));
                app.Stop(Seconds(tStop));
                f.app = app.Get(0);
            }
        }
        else
        {
            BulkSendHelper bulk(factory, dst);
            bulk.SetAttribute("MaxBytes", UintegerValue(0));
            ApplicationContainer app = bulk.Install(nodes.Get(from));
            app.Start(Seconds(f.startAt));
            app.Stop(Seconds(tStop));
            f.app = app.Get(0);
        }
        if (f.udp)
        {
            if (f.app)
            {
                f.app->TraceConnectWithoutContext("Tx", MakeBoundCallback(&UdpTx, &f));
            }
            f.sink->TraceConnectWithoutContext("Rx", MakeBoundCallback(&UdpRx, &f));
        }
        else if (f.app)
        {
            // the flow's TCP type: the sending host makes its next socket of that type, just before the flow starts
            Ptr<Node> node = nodes.Get(from);
            std::string type = f.type;
            Simulator::Schedule(Seconds(f.startAt) - NanoSeconds(1), [node, type] {
                node->GetObject<TcpL4Protocol>()->SetAttribute("SocketType", TypeIdValue(TypeId::LookupByName("ns3::" + type)));
            });
            FlowState* fp = &f;
            Simulator::Schedule(Seconds(f.startAt) + MicroSeconds(1), [fp] {
                Ptr<Socket> s = DynamicCast<SourceApplication>(fp->app)->GetSocket();
                if (s)
                {
                    s->TraceConnectWithoutContext("CongestionWindow", MakeBoundCallback(&Cwnd, fp));
                    s->TraceConnectWithoutContext("Retransmission", MakeBoundCallback(&Retrans, fp));
                }
            });
        }
    }

    // ---- sampling: a row every 0.1 s, and the counters at both ends of the measured seconds
    std::ofstream csv(out + "/series.csv");
    csv << "t";
    for (auto& f : flows)
    {
        csv << "," << f.id << "_bps";
        if (!f.udp)
        {
            csv << "," << f.id << "_cwnd";
        }
    }
    for (auto& l : links)
    {
        for (uint32_t side = 0; side < 2; side++)
        {
            const QueueSpec& q = l.q[side];
            if (!q.given)
            {
                continue;
            }
            if (q.kind == "scheduler")
            {
                for (auto& [fid, part] : q.parts)
                {
                    csv << "," << l.id << "_q_" << fid << "," << l.id << "_drops_" << fid;
                }
            }
            else
            {
                const char* back = l.q[0].given && l.q[1].given && side == 1 ? "_back" : ""; // two described plain queues on one link are told apart
                csv << "," << l.id << "_q" << back << "," << l.id << "_drops" << back;
            }
        }
    }
    csv << "\n";
    const double period = 0.1;
    std::function<void()> sample = [&]() {
        csv << std::fixed << std::setprecision(3) << Simulator::Now().GetSeconds();
        for (auto& f : flows)
        {
            uint64_t rx = f.sink->GetTotalRx();
            csv << "," << std::setprecision(0) << (rx - f.lastRx) * 8.0 / period;
            f.lastRx = rx;
            if (!f.udp)
            {
                csv << "," << f.cwnd;
            }
        }
        for (auto& l : links)
        {
            for (uint32_t side = 0; side < 2; side++)
            {
                const QueueSpec& q = l.q[side];
                if (!q.given)
                {
                    continue;
                }
                if (q.kind == "scheduler")
                {
                    for (uint32_t i = 0; i < q.parts.size(); i++)
                    {
                        Ptr<QueueDisc> c = l.root[side]->GetQueueDiscClass(i)->GetQueueDisc();
                        csv << "," << c->GetNPackets() << "," << c->GetStats().nTotalDroppedPackets;
                    }
                }
                else
                {
                    csv << "," << l.root[side]->GetNPackets() << "," << l.root[side]->GetStats().nTotalDroppedPackets;
                }
            }
        }
        csv << "\n";
        csv.flush(); // a run can be watched while it runs
        if (Simulator::Now().GetSeconds() + period <= tStop + 1e-9)
        {
            Simulator::Schedule(Seconds(period), [&sample] { sample(); });
        }
    };
    Simulator::Schedule(Seconds(tStart + period), [&sample] { sample(); });
    auto take = [&](bool end) {
        for (auto& f : flows)
        {
            (end ? f.rx1 : f.rx0) = f.sink->GetTotalRx();
            (end ? f.retrans1 : f.retrans0) = f.retrans;
        }
        for (auto& l : links)
        {
            for (uint32_t side = 0; side < 2; side++)
            {
                (end ? l.tx1 : l.tx0)[side] = l.tx[side];
                (end ? l.drops1 : l.drops0)[side] = Drops(l.root[side]);
            }
        }
    };
    Simulator::Schedule(Seconds(tMeasure), [&take] { take(false); });
    Simulator::Schedule(Seconds(tStop), [&take] { take(true); });

    Simulator::Stop(Seconds(tStop + 1.0));
    Simulator::Run();

    // ---- the measures
    std::ofstream m(out + "/metrics.json");
    m << "{\n";
    bool first = true;
    auto put = [&](const std::string& k, double v, int digits) {
        m << (first ? "" : ",\n") << "  \"" << k << "\": " << std::fixed << std::setprecision(digits) << v;
        first = false;
    };
    for (auto& f : flows)
    {
        put(f.id + "_goodput_bps", (f.rx1 - f.rx0) * 8.0 / duration, 0);
        if (f.udp)
        {
            put(f.id + "_loss_frac", f.txWin ? 1.0 - double(f.rxWin) / double(f.txWin) : 0.0, 6);
        }
        else
        {
            put(f.id + "_retrans", double(f.retrans1 - f.retrans0), 0);
        }
    }
    for (auto& l : links)
    {
        double bps0 = double(DataRate(l.rateOf[0].empty() ? l.rate : l.rateOf[0]).GetBitRate());
        double bps1 = double(DataRate(l.rateOf[1].empty() ? l.rate : l.rateOf[1]).GetBitRate());
        put(l.id + "_util", (l.tx1[0] - l.tx0[0]) * 8.0 / duration / bps0, 6);
        put(l.id + "_util_back", (l.tx1[1] - l.tx0[1]) * 8.0 / duration / bps1, 6);
        bool given = l.q[0].given || l.q[1].given;
        bool both = l.q[0].given && l.q[1].given; // a described queue on each side: the plain one of b's side is "back"
        for (uint32_t side = 0; side < 2; side++)
        {
            const QueueSpec& q = l.q[side];
            if (q.given && q.kind == "scheduler")
            {
                for (uint32_t i = 0; i < q.parts.size(); i++)
                {
                    put(l.id + "_drops_" + q.parts[i].first, double(l.drops1[side][i] - l.drops0[side][i]), 0);
                }
            }
            else if (q.given)
            {
                put(l.id + (both && side == 1 ? "_drops_back" : "_drops"), double(l.drops1[side][0] - l.drops0[side][0]), 0);
            }
            else
            {
                // a side without a described queue: when the link has one on its other side this is "back";
                // a link with no described queue at all reports its two plain queues as <link>_drops and <link>_drops_back
                put(l.id + (given || side == 1 ? "_drops_back" : "_drops"), double(l.drops1[side][0] - l.drops0[side][0]), 0);
            }
        }
    }
    m << "\n}\n";
    m.close();
    Simulator::Destroy();
    return 0;
}
