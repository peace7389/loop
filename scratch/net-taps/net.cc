// net: a network built from a description. Hosts joined by point-to-point links, UDP and TCP flows between them,
// a plain queue or the scheduler (FlowQueueDisc) on the sending side of a link.
//
//   net --net=/abs/network.txt --out=/abs/dir
//
// network.txt, one object per line (words, then name=value pairs; a line that starts with # is skipped):
//   host  <id>
//   link  <id> <host> <host> rate=1Gbps delay=50us mtu=1500 devq=10
//   dev   <link> <host> [rate=1Gbps] [devq=10] [mtu=1500] [loss=0.01]   the device of that host on that link, where it differs from the link's line;
//         loss: the part of the packets arriving at this device that it receives in error and drops (ns-3: a RateErrorModel as its ReceiveErrorModel)
//   queue <link> <host> kind=fifo|scheduler|pfifofast|codel|fqcodel|red|pie length=100 [parts=<name>:<part>,...] [largest=<name>:<rate>,...] [classes=<name>:<flow>+<flow>,...]
//         the queue disc of that device: ns-3's FifoQueueDisc, PfifoFastQueueDisc, CoDelQueueDisc, FqCoDelQueueDisc, RedQueueDisc, PieQueueDisc (each with
//         ns-3's own settings and length as its MaxSize), or scheduler, this project's FlowQueueDisc
//         a part's name is a flow (that flow has a queue of its own), or a class: several flows that share one queue of the scheduler
//   flow  <id> udp <from> <to> rate=2Gbps packet=1400
//   flow  <id> tcp <from> <to> type=TcpCubic [app=onoff rate=200Mbps packet=1400]
//         udp or tcp is the socket the application opens (ns-3: its Protocol, a socket factory). app is the ns-3 application
//         that sends: onoff (OnOffApplication, always on: packets at a constant rate) or bulk (BulkSendApplication: as fast
//         as the socket accepts; it needs a TCP socket). Left out, a udp flow is onoff and a tcp flow is bulk.
//         a flow line may also say start=<s> stop=<s> (the application's StartTime and StopTime, in seconds of the simulation; left out: 1 s and the
//         end), on=<s> off=<s> (OnOff only: the lengths of its on and off periods; left out: always on) and maxbytes=<n> (it stops after that many bytes)
//   tcp   [initcwnd=10] [buf=1048576] [sack=0|1] [timestamps=0|1] [delack=2]   for every TCP socket (ns-3's defaults where left out)
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
//   <link>_lost_<host>            packets the device of that host received in error and dropped (only for a device with loss=)
#include "flow-queue-disc.h"

#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/traffic-control-module.h"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
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
    double start = -1, stop = -1, on = -1, off = -1; // StartTime, StopTime, the on and off periods, in seconds (below 0: not stated)
    uint64_t maxBytes = 0;                           // MaxBytes (0: no limit)
    Ptr<PacketSink> sink;
    Ptr<Application> app;
    // counters
    uint64_t txWin = 0, rxWin = 0, uidFirst = 0, uidLast = 0, retrans = 0;
    uint32_t cwnd = 0;
    uint64_t lastRx = 0, rx0 = 0, rx1 = 0, retrans0 = 0, retrans1 = 0;
    // the probe (--probe): what TCP last reported, and the bytes received at the probe's last sample
    uint32_t ssthresh = 0, inflight = 0, rwnd = 0;
    double rttMs = 0, rtoMs = 0;
    uint64_t probeRx = 0;
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
    uint32_t mtuOf[2] = {0, 0};  // its largest packet (0: the link's)
    double lossOf[2] = {-1, -1}; // the part of the packets it receives in error (below 0: no error model)
    uint64_t lost[2] = {0, 0}, lost0[2] = {0, 0}, lost1[2] = {0, 0};
    std::vector<double> waitMs[2]; // the probe: the longest time a packet leaving each queue of that side had waited, since the last sample
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

// ---- taps (--taps=<file>, with --probe): trace sources the researcher names by their ns-3 Config path (2026-11-22, the operator: measurements
// of its own, on demand). Each line of the file: <name> <path>, the path ending with the trace source's name, for example
//   cwnd  /NodeList/0/$ns3::TcpL4Protocol/SocketList/0/CongestionWindow
//   drops /NodeList/0/DeviceList/0/$ns3::PointToPointNetDevice/TxQueue/Drop
// A tap is connected once the object exists (tried from the first flow's start, then every 0.05 s); its kind is read from ns-3's TypeId: a value
// (a TracedValue: Uint32, Int32, Double, Bool, Time in ms, SequenceNumber32, DataRate in bps, TCP's congestion state) stands in probe.csv as
// tap_<name>, its last value at each row (empty until its first change); an event (a packet or queue item callback, IPv4's send, receive and
// drop, TCP's retransmission and segments) stands as tap_<name>_n and tap_<name>_bytes, its count and bytes since the last row. It only listens:
// no packet is sent, held or dropped by it and no random number is drawn. taps.json says what each line matched and how it was connected or why
// not. --listtaps=<file> writes, 10 ms after the last flow's start (every socket exists), every object a tap can name with its trace sources, and stops.
struct Tap
{
    std::string name, path, src, kind = "none", callback, why = "not tried", type;
    uint32_t matched = 0;
    double value = std::numeric_limits<double>::quiet_NaN();
    uint64_t n = 0, bytes = 0;
};
static void TapU32(Tap* t, uint32_t, uint32_t v) { t->value = v; t->n++; }
static void TapI32(Tap* t, int32_t, int32_t v) { t->value = v; t->n++; }
static void TapDbl(Tap* t, double, double v) { t->value = v; t->n++; }
static void TapBool(Tap* t, bool, bool v) { t->value = v ? 1 : 0; t->n++; }
static void TapTime(Tap* t, Time, Time v) { t->value = v.GetSeconds() * 1e3; t->n++; }
static void TapSeq(Tap* t, SequenceNumber32, SequenceNumber32 v) { t->value = v.GetValue(); t->n++; }
static void TapRate(Tap* t, DataRate, DataRate v) { t->value = v.GetBitRate(); t->n++; }
static void TapCong(Tap* t, TcpSocketState::TcpCongState_t, TcpSocketState::TcpCongState_t v) { t->value = static_cast<int>(v); t->n++; }
static void TapTimeCb(Tap* t, Time v) { t->value = v.GetSeconds() * 1e3; t->n++; }
static void TapPkt(Tap* t, Ptr<const Packet> p) { t->n++; t->bytes += p->GetSize(); }
static void TapItem(Tap* t, Ptr<const QueueDiscItem> i) { t->n++; t->bytes += i->GetSize(); }
static void TapIpTxRx(Tap* t, Ptr<const Packet> p, Ptr<Ipv4>, uint32_t) { t->n++; t->bytes += p->GetSize(); }
static void TapIpSent(Tap* t, const Ipv4Header&, Ptr<const Packet> p, uint32_t) { t->n++; t->bytes += p->GetSize(); }
static void TapIpDrop(Tap* t, const Ipv4Header&, Ptr<const Packet> p, Ipv4L3Protocol::DropReason, Ptr<Ipv4>, uint32_t) { t->n++; t->bytes += p->GetSize(); }
static void TapTcpTxRx(Tap* t, const Ptr<const Packet> p, const TcpHeader&, const Ptr<const TcpSocketBase>) { t->n++; t->bytes += p->GetSize(); }
static void TapTcpRetx(Tap* t, const Ptr<const Packet> p, const TcpHeader&, const Address&, const Address&, const Ptr<const TcpSocketBase>) { t->n++; t->bytes += p->GetSize(); }
// the trace sources of an object's type, its parents' included: name -> information
static std::map<std::string, TypeId::TraceSourceInformation>
TraceSourcesOf(TypeId tid)
{
    std::map<std::string, TypeId::TraceSourceInformation> out;
    for (TypeId t = tid;; t = t.GetParent())
    {
        for (std::size_t i = 0; i < t.GetTraceSourceN(); i++)
        {
            TypeId::TraceSourceInformation info = t.GetTraceSource(i);
            out.emplace(info.name, info);
        }
        if (t == t.GetParent())
        {
            break;
        }
    }
    return out;
}
// connect one tap; false while the object is not there yet (the caller tries again later)
static bool
ConnectTap(Tap& t)
{
    auto cut = t.path.rfind('/');
    if (cut == std::string::npos || cut == 0 || t.path[0] != '/')
    {
        t.why = "a path begins with / and ends with the name of a trace source, for example /NodeList/0/DeviceList/0/$ns3::PointToPointNetDevice/MacTx";
        t.kind = "refused";
        return true;
    }
    std::string base = t.path.substr(0, cut);
    t.src = t.path.substr(cut + 1);
    Config::MatchContainer m = Config::LookupMatches(base);
    t.matched = m.GetN();
    if (m.GetN() == 0)
    {
        t.why = "no object at " + base + " (yet)";
        return false;
    }
    if (m.GetN() > 1)
    {
        t.why = "the path names " + std::to_string(m.GetN()) + " objects: name one (no * and no ranges)";
        t.kind = "refused";
        return true;
    }
    Ptr<Object> o = m.Get(0);
    TypeId tid = o->GetInstanceTypeId();
    t.type = tid.GetName();
    auto all = TraceSourcesOf(tid);
    auto it = all.find(t.src);
    if (it == all.end())
    {
        std::string names;
        for (auto& [k, v] : all)
        {
            names += (names.empty() ? "" : ", ") + k;
        }
        t.why = t.type + " has no trace source " + t.src + "; it has: " + names;
        t.kind = "refused";
        return true;
    }
    t.callback = it->second.callback;
    const std::string& c = t.callback;
    bool ok = false;
    std::string kind = "value";
    if (c == "ns3::TracedValueCallback::Uint32") ok = o->TraceConnectWithoutContext(t.src, MakeBoundCallback(&TapU32, &t));
    else if (c == "ns3::TracedValueCallback::Int32") ok = o->TraceConnectWithoutContext(t.src, MakeBoundCallback(&TapI32, &t));
    else if (c == "ns3::TracedValueCallback::Double") ok = o->TraceConnectWithoutContext(t.src, MakeBoundCallback(&TapDbl, &t));
    else if (c == "ns3::TracedValueCallback::Bool") ok = o->TraceConnectWithoutContext(t.src, MakeBoundCallback(&TapBool, &t));
    else if (c == "ns3::TracedValueCallback::Time") ok = o->TraceConnectWithoutContext(t.src, MakeBoundCallback(&TapTime, &t));
    else if (c == "ns3::TracedValueCallback::SequenceNumber32") ok = o->TraceConnectWithoutContext(t.src, MakeBoundCallback(&TapSeq, &t));
    else if (c == "ns3::TracedValueCallback::DataRate") ok = o->TraceConnectWithoutContext(t.src, MakeBoundCallback(&TapRate, &t));
    else if (c == "ns3::TcpSocketState::TcpCongStatesTracedValueCallback") ok = o->TraceConnectWithoutContext(t.src, MakeBoundCallback(&TapCong, &t));
    else if (c == "ns3::Time::TracedCallback") ok = o->TraceConnectWithoutContext(t.src, MakeBoundCallback(&TapTimeCb, &t)), kind = "time event";
    else
    {
        kind = "event";
        if (c == "ns3::Packet::TracedCallback") ok = o->TraceConnectWithoutContext(t.src, MakeBoundCallback(&TapPkt, &t));
        else if (c == "ns3::QueueDiscItem::TracedCallback") ok = o->TraceConnectWithoutContext(t.src, MakeBoundCallback(&TapItem, &t));
        else if (c == "ns3::Ipv4L3Protocol::TxRxTracedCallback") ok = o->TraceConnectWithoutContext(t.src, MakeBoundCallback(&TapIpTxRx, &t));
        else if (c == "ns3::Ipv4L3Protocol::SentTracedCallback") ok = o->TraceConnectWithoutContext(t.src, MakeBoundCallback(&TapIpSent, &t));
        else if (c == "ns3::Ipv4L3Protocol::DropTracedCallback") ok = o->TraceConnectWithoutContext(t.src, MakeBoundCallback(&TapIpDrop, &t));
        else if (c == "ns3::TcpSocketBase::TcpTxRxTracedCallback") ok = o->TraceConnectWithoutContext(t.src, MakeBoundCallback(&TapTcpTxRx, &t));
        else if (c == "ns3::TcpSocketBase::RetransmissionCallback") ok = o->TraceConnectWithoutContext(t.src, MakeBoundCallback(&TapTcpRetx, &t));
        else
        {
            t.why = "its kind (" + c + ") cannot be recorded yet: values (TracedValue) and packet events can";
            t.kind = "refused";
            return true;
        }
    }
    t.kind = ok ? kind : "refused";
    t.why = ok ? "connected at " + std::to_string(Simulator::Now().GetSeconds()) + " s" : "ns-3 did not connect it";
    return true;
}
static std::string
JsonText(const std::string& s)
{
    std::string o = "\"";
    for (char ch : s)
    {
        if (ch == '"' || ch == '\\') o += '\\';
        if (ch == '\n') { o += "\\n"; continue; }
        o += ch;
    }
    return o + "\"";
}
// every object a tap can name, with its trace sources (--listtaps)
static void
ListTaps(const std::string& file)
{
    std::ofstream o(file);
    o << "[";
    bool first = true;
    for (const char* pat : {"/NodeList/*/DeviceList/*", "/NodeList/*/DeviceList/*/$ns3::PointToPointNetDevice/TxQueue", "/NodeList/*/$ns3::TrafficControlLayer/RootQueueDiscList/*",
                            "/NodeList/*/$ns3::Ipv4L3Protocol", "/NodeList/*/$ns3::TcpL4Protocol/SocketList/*", "/NodeList/*/ApplicationList/*", "/ChannelList/*"})
    {
        Config::MatchContainer m = Config::LookupMatches(pat);
        for (std::size_t i = 0; i < m.GetN(); i++)
        {
            TypeId tid = m.Get(i)->GetInstanceTypeId();
            o << (first ? "\n" : ",\n") << " {\"path\": " << JsonText(m.GetMatchedPath(i)) << ", \"type\": " << JsonText(tid.GetName()) << ", \"sources\": [";
            first = false;
            bool f2 = true;
            for (auto& [k, v] : TraceSourcesOf(tid))
            {
                o << (f2 ? "" : ", ") << "{\"name\": " << JsonText(k) << ", \"callback\": " << JsonText(v.callback) << ", \"help\": " << JsonText(v.help) << "}";
                f2 = false;
            }
            o << "]}";
        }
    }
    o << "\n]\n";
}

// ---- the probe (--probe=<seconds>): a second, finer record, probe.csv. It only listens (trace sinks, and a sampler of its own): nothing
// that sends, queues, drops or times a packet is added, and no random number is drawn. The harness keeps the file only when the
// simulation run again with it gives metrics.json and series.csv byte for byte as without it.
static void
PSsThresh(FlowState* f, uint32_t, uint32_t now)
{
    f->ssthresh = now;
}
static void
PInFlight(FlowState* f, uint32_t, uint32_t now)
{
    f->inflight = now;
}
static void
PRwnd(FlowState* f, uint32_t, uint32_t now)
{
    f->rwnd = now;
}
static void
PRtt(FlowState* f, Time, Time now)
{
    f->rttMs = now.GetSeconds() * 1e3;
}
static void
PRto(FlowState* f, Time, Time now)
{
    f->rtoMs = now.GetSeconds() * 1e3;
}
static void
PWait(double* w, Time t)
{
    *w = std::max(*w, t.GetSeconds() * 1e3);
}

static void
LinkLost(LinkState* l, uint32_t side, Ptr<const Packet>)
{
    ++l->lost[side];
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
Drops(Ptr<QueueDisc> root, bool scheduler)
{
    std::vector<uint32_t> d;
    if (!scheduler) // one figure for a queue disc of ns-3's own, whatever classes it makes for itself (FqCoDel: one for each flow)
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
    double probe = 0;
    std::string tapsFile, listTaps;
    CommandLine cmd(__FILE__);
    cmd.AddValue("taps", "Absolute path of a file of taps (<name> <ns-3 Config path of a trace source>), recorded in probe.csv (with --probe)", tapsFile);
    cmd.AddValue("listtaps", "Absolute path: write every object a tap can name, with its trace sources, at the first flow's start, and stop", listTaps);
    cmd.AddValue("net", "Absolute path of the network description", netFile);
    cmd.AddValue("out", "Absolute output directory", out);
    cmd.AddValue("probe", "Seconds between the samples of probe.csv, a finer record that only listens (0 = none)", probe);
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
    uint32_t seed = 1, initCwnd = 0, bufBytes = 0, delAck = 0;
    int sack = -1, timestamps = -1; // TCP's options: below 0, ns-3's default (both on)
    const std::map<std::string, std::string> discOf = {{"fifo", "ns3::FifoQueueDisc"},   {"pfifofast", "ns3::PfifoFastQueueDisc"},
                                                       {"codel", "ns3::CoDelQueueDisc"}, {"fqcodel", "ns3::FqCoDelQueueDisc"},
                                                       {"red", "ns3::RedQueueDisc"},     {"pie", "ns3::PieQueueDisc"}};
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
            l.mtuOf[side] = m.count("mtu") ? std::stoul(m["mtu"]) : l.mtuOf[side];
            l.lossOf[side] = m.count("loss") ? std::stod(m["loss"]) : l.lossOf[side];
            NS_ABORT_MSG_IF(l.lossOf[side] > 1, "dev: loss is a part of the packets, from 0 to 1");
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
            NS_ABORT_MSG_IF(q.kind != "scheduler" && !discOf.count(q.kind), "queue kind must be scheduler, fifo, pfifofast, codel, fqcodel, red or pie");
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
            f.start = m.count("start") ? std::stod(m["start"]) : f.start;
            f.stop = m.count("stop") ? std::stod(m["stop"]) : f.stop;
            f.on = m.count("on") ? std::stod(m["on"]) : f.on;
            f.off = m.count("off") ? std::stod(m["off"]) : f.off;
            f.maxBytes = m.count("maxbytes") ? std::stoull(m["maxbytes"]) : f.maxBytes;
            NS_ABORT_MSG_IF((f.on >= 0) != (f.off >= 0), "flow '" << f.id << "': on= and off= are given together");
            NS_ABORT_MSG_IF(f.on >= 0 && !f.onoff, "flow '" << f.id << "': BulkSendApplication has no on and off periods");
            NS_ABORT_MSG_IF(f.on >= 0 && f.on <= 0, "flow '" << f.id << "': the on period is longer than 0");
            f.port = 9000 + flows.size();
            flows.push_back(f);
        }
        else if (what == "tcp")
        {
            auto m = Pairs(ls);
            initCwnd = m.count("initcwnd") ? std::stoul(m["initcwnd"]) : 0;
            bufBytes = m.count("buf") ? std::stoul(m["buf"]) : 0;
            sack = m.count("sack") ? std::stoi(m["sack"]) : sack;
            timestamps = m.count("timestamps") ? std::stoi(m["timestamps"]) : timestamps;
            delAck = m.count("delack") ? std::stoul(m["delack"]) : delAck;
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
        for (uint32_t side = 0; side < 2; side++)
        {
            minMtu = l.mtuOf[side] ? std::min(minMtu, l.mtuOf[side]) : minMtu;
        }
    }
    // 20 IP + 20 TCP + 12 timestamp option: a full segment is one packet of the smallest MTU on the way
    Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(minMtu - (timestamps == 0 ? 40 : 52)));
    if (sack >= 0)
    {
        Config::SetDefault("ns3::TcpSocketBase::Sack", BooleanValue(sack != 0));
    }
    if (timestamps >= 0)
    {
        Config::SetDefault("ns3::TcpSocketBase::Timestamp", BooleanValue(timestamps != 0));
    }
    if (delAck)
    {
        Config::SetDefault("ns3::TcpSocket::DelAckCount", UintegerValue(delAck));
    }
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
            if (l.mtuOf[side])
            {
                l.devs.Get(side)->SetAttribute("Mtu", UintegerValue(l.mtuOf[side]));
            }
            if (l.lossOf[side] >= 0)
            {
                Ptr<RateErrorModel> em = CreateObject<RateErrorModel>();
                em->SetAttribute("ErrorRate", DoubleValue(l.lossOf[side]));
                em->SetAttribute("ErrorUnit", EnumValue(RateErrorModel::ERROR_UNIT_PACKET));
                l.devs.Get(side)->SetAttribute("ReceiveErrorModel", PointerValue(em));
                l.devs.Get(side)->TraceConnectWithoutContext("PhyRxDrop", MakeBoundCallback(&LinkLost, &l, side));
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
                tch.SetRootQueueDisc(discOf.at(q.kind), "MaxSize", StringValue(size));
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
            if (probe > 0 && q.given) // how long a packet waited in each described queue (ns-3's SojournTime, which every queue disc reports)
            {
                l.waitMs[side].assign(q.kind == "scheduler" ? q.parts.size() : 1, 0.0);
                for (uint32_t i = 0; i < l.waitMs[side].size(); i++)
                {
                    Ptr<QueueDisc> d = q.kind == "scheduler" ? l.root[side]->GetQueueDiscClass(i)->GetQueueDisc() : l.root[side];
                    d->TraceConnectWithoutContext("SojournTime", MakeBoundCallback(&PWait, &l.waitMs[side][i]));
                }
            }
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
        // each flow starts up to 10 ms after its start time (tStart where none is stated); the offsets depend on the seed
        f.startAt = std::max((f.start >= 0 ? f.start : tStart) + offset->GetValue(0.0, 0.01), 1e-6);
        const double stopAt = f.stop >= 0 ? std::min(f.stop, tStop) : tStop;
        NS_ABORT_MSG_IF(stopAt <= f.startAt, "flow '" << f.id << "' stops before it starts");
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
                if (f.on >= 0)
                {
                    onoff.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=" + std::to_string(f.on) + "]"));
                    onoff.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=" + std::to_string(f.off) + "]"));
                }
                onoff.SetAttribute("MaxBytes", UintegerValue(f.maxBytes));
                ApplicationContainer app = onoff.Install(nodes.Get(from));
                app.Start(Seconds(f.startAt));
                app.Stop(Seconds(stopAt));
                f.app = app.Get(0);
            }
        }
        else
        {
            BulkSendHelper bulk(factory, dst);
            bulk.SetAttribute("MaxBytes", UintegerValue(f.maxBytes));
            ApplicationContainer app = bulk.Install(nodes.Get(from));
            app.Start(Seconds(f.startAt));
            app.Stop(Seconds(stopAt));
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
            if (probe > 0)
            {
                Simulator::Schedule(Seconds(f.startAt) + MicroSeconds(1), [fp] {
                    Ptr<Socket> s = DynamicCast<SourceApplication>(fp->app)->GetSocket();
                    if (s)
                    {
                        s->TraceConnectWithoutContext("SlowStartThreshold", MakeBoundCallback(&PSsThresh, fp));
                        s->TraceConnectWithoutContext("BytesInFlight", MakeBoundCallback(&PInFlight, fp));
                        s->TraceConnectWithoutContext("RWND", MakeBoundCallback(&PRwnd, fp));
                        s->TraceConnectWithoutContext("RTT", MakeBoundCallback(&PRtt, fp));
                        s->TraceConnectWithoutContext("RTO", MakeBoundCallback(&PRto, fp));
                    }
                });
            }
        }
    }

    // ---- taps: read the file; each is connected once its object exists, from the first flow's start, then every 0.05 s (sockets exist only then)
    std::vector<Tap> taps;
    double firstStart = tStop, lastStart = 0;
    for (auto& f : flows)
    {
        firstStart = std::min(firstStart, f.startAt);
        lastStart = std::max(lastStart, f.startAt);
    }
    if (!tapsFile.empty())
    {
        std::ifstream tf(tapsFile);
        std::string name, path;
        while (tf >> name >> path)
        {
            Tap tp;
            tp.name = name;
            tp.path = path;
            taps.push_back(tp);
        }
    }
    std::function<void()> tryTaps = [&]() {   // the vector is complete before this runs: the bound pointers stay valid
        bool left = false;
        for (auto& tp : taps)
        {
            if (tp.kind == "none" && !ConnectTap(tp))
            {
                left = true;
            }
        }
        if (left && Simulator::Now().GetSeconds() + 0.05 <= tStop)
        {
            Simulator::Schedule(Seconds(0.05), [&tryTaps] { tryTaps(); });
        }
    };
    if (!taps.empty())
    {
        Simulator::Schedule(Seconds(firstStart) + MicroSeconds(2), [&tryTaps] { tryTaps(); });
    }
    if (!listTaps.empty())
    {
        Simulator::Schedule(Seconds(lastStart) + MilliSeconds(10), [&listTaps] {   // every flow has started and its connection is made: every socket exists
            ListTaps(listTaps);
            Simulator::Stop();
        });
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
    // ---- the probe's own record: a row every `probe` seconds. Per flow its bits per second over the row; per TCP flow what its socket last
    // reported; per described queue the longest wait of a packet that left it since the last row, and the packets waiting; per device its transmit queue
    std::ofstream pcsv;
    const double pper = std::max(probe, 0.001);
    std::function<void()> psample = [&]() {
        pcsv << std::fixed << std::setprecision(4) << Simulator::Now().GetSeconds();
        for (auto& f : flows)
        {
            uint64_t rx = f.sink->GetTotalRx();
            pcsv << "," << std::setprecision(0) << (rx - f.probeRx) * 8.0 / pper;
            f.probeRx = rx;
            if (!f.udp)
            {
                pcsv << "," << f.cwnd << "," << f.ssthresh << "," << f.inflight << "," << f.rwnd << "," << std::setprecision(3) << f.rttMs << "," << f.rtoMs;
            }
        }
        for (auto& l : links)
        {
            for (uint32_t side = 0; side < 2; side++)
            {
                const QueueSpec& q = l.q[side];
                for (uint32_t i = 0; i < l.waitMs[side].size(); i++)
                {
                    Ptr<QueueDisc> d = q.kind == "scheduler" ? l.root[side]->GetQueueDiscClass(i)->GetQueueDisc() : l.root[side];
                    pcsv << "," << std::setprecision(3) << l.waitMs[side][i] << "," << d->GetNPackets();
                    l.waitMs[side][i] = 0;
                }
                pcsv << "," << DynamicCast<PointToPointNetDevice>(l.devs.Get(side))->GetQueue()->GetNPackets();
            }
        }
        for (auto& tp : taps)
        {
            bool val = tp.kind == "value" || tp.kind == "time event", ev = tp.kind == "event";
            pcsv << "," << std::setprecision(6);
            if (val && !std::isnan(tp.value)) pcsv << tp.value; else pcsv << "nan";
            if (val || ev) pcsv << "," << tp.n; else pcsv << ",nan";
            if (ev) pcsv << "," << tp.bytes; else pcsv << ",nan";
            tp.n = 0;
            tp.bytes = 0;
        }
        pcsv << "\n";
        if (Simulator::Now().GetSeconds() + pper <= tStop + 1e-9)
        {
            Simulator::Schedule(Seconds(pper), [&psample] { psample(); });
        }
    };
    if (probe > 0)
    {
        pcsv.open(out + "/probe.csv");
        pcsv << "t";
        for (auto& f : flows)
        {
            pcsv << "," << f.id << "_bps";
            if (!f.udp)
            {
                pcsv << "," << f.id << "_cwnd," << f.id << "_ssthresh," << f.id << "_inflight," << f.id << "_rwnd," << f.id << "_rtt_ms," << f.id << "_rto_ms";
            }
        }
        for (auto& l : links)
        {
            for (uint32_t side = 0; side < 2; side++)
            {
                const QueueSpec& q = l.q[side];
                const char* back = l.q[0].given && l.q[1].given && side == 1 ? "_back" : "";
                for (uint32_t i = 0; i < l.waitMs[side].size(); i++)
                {
                    std::string name = q.kind == "scheduler" ? "_" + q.parts[i].first : std::string(back);
                    pcsv << "," << l.id << "_wait" << name << "_ms," << l.id << "_q" << name;
                }
                pcsv << "," << l.id << "_devq" << (side == 1 ? "_back" : "");
            }
        }
        for (auto& tp : taps)
        {
            pcsv << ",tap_" << tp.name << ",tap_" << tp.name << "_n,tap_" << tp.name << "_bytes";
        }
        pcsv << "\n";
        Simulator::Schedule(Seconds(tStart + pper), [&psample] { psample(); });
    }
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
                (end ? l.drops1 : l.drops0)[side] = Drops(l.root[side], l.q[side].kind == "scheduler");
                (end ? l.lost1 : l.lost0)[side] = l.lost[side];
            }
        }
    };
    Simulator::Schedule(Seconds(tMeasure), [&take] { take(false); });
    Simulator::Schedule(Seconds(tStop), [&take] { take(true); });

    Simulator::Stop(Seconds(tStop + 1.0));
    Simulator::Run();
    if (!listTaps.empty())   // only the list of what a tap can name: nothing else is written
    {
        Simulator::Destroy();
        return 0;
    }
    if (!taps.empty())
    {
        std::ofstream tj(out + "/taps.json");
        tj << "[";
        for (std::size_t i = 0; i < taps.size(); i++)
        {
            const Tap& tp = taps[i];
            tj << (i ? ",\n " : "\n ") << "{\"name\": " << JsonText(tp.name) << ", \"path\": " << JsonText(tp.path) << ", \"type\": " << JsonText(tp.type) << ", \"source\": " << JsonText(tp.src)
               << ", \"callback\": " << JsonText(tp.callback) << ", \"kind\": " << JsonText(tp.kind) << ", \"matched\": " << tp.matched << ", \"why\": " << JsonText(tp.why) << "}";
        }
        tj << "\n]\n";
    }

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
        for (uint32_t side = 0; side < 2; side++)
        {
            if (l.lossOf[side] >= 0)
            {
                put(l.id + "_lost_" + (side == 0 ? l.a : l.b), double(l.lost1[side] - l.lost0[side]), 0);
            }
        }
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
