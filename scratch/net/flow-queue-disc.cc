#include "flow-queue-disc.h"

#include "ns3/abort.h"
#include "ns3/ipv4-queue-disc-item.h"
#include "ns3/log.h"
#include "ns3/net-device-queue-interface.h"
#include "ns3/net-device.h"
#include "ns3/simulator.h"
#include "ns3/tcp-header.h"
#include "ns3/udp-header.h"
#include "ns3/uinteger.h"

#include <algorithm>
#include <cstdlib>
#include <string>

namespace ns3
{

NS_LOG_COMPONENT_DEFINE("FlowQueueDisc");
NS_OBJECT_ENSURE_REGISTERED(FlowQueueDisc);

TypeId
FlowQueueDisc::GetTypeId()
{
    static TypeId tid = TypeId("ns3::FlowQueueDisc")
                            .SetParent<QueueDisc>()
                            .SetGroupName("TrafficControl")
                            .AddConstructor<FlowQueueDisc>()
                            .AddAttribute("Quantum",
                                          "Bytes a band of part 1 gets per round (share); the most a band sends at once (cap, largest rate)",
                                          UintegerValue(3000),
                                          MakeUintegerAccessor(&FlowQueueDisc::m_quantum),
                                          MakeUintegerChecker<uint32_t>(1));
    return tid;
}

FlowQueueDisc::FlowQueueDisc()
    : QueueDisc(QueueDiscSizePolicy::NO_LIMITS),
      m_mode(SHARE),
      m_cur(0)
{
    const char* env = std::getenv("TWOHOSTS_SCHED");
    const std::string mode = env ? env : "share";
    NS_ABORT_MSG_IF(mode != "share" && mode != "cap" && mode != "prio",
                    "TWOHOSTS_SCHED must be share, cap or prio, got '" << mode << "'");
    m_mode = (mode == "cap") ? CAP : (mode == "prio") ? PRIO : SHARE;
}

FlowQueueDisc::~FlowQueueDisc()
{
}

void
FlowQueueDisc::SetBands(const std::vector<Band>& bands)
{
    NS_ABORT_MSG_IF(bands.empty(), "a scheduler needs at least one band");
    m_bands = bands;
    double sum = 0;
    for (const Band& b : bands)
    {
        NS_ABORT_MSG_IF(b.part <= 0, "a band's part of the link must be above 0");
        sum += b.part;
    }
    m_w.clear();
    m_bandOf.clear();
    for (uint32_t i = 0; i < bands.size(); i++)
    {
        m_w.push_back(bands[i].part / sum);
        m_bandOf[bands[i].port] = i;
    }
}

// A packet in a queue disc starts with its transport header; the IP header is kept beside it.
bool
FlowQueueDisc::DoEnqueue(Ptr<QueueDiscItem> item)
{
    uint32_t band = m_bands.size(); // everything else
    Ptr<Ipv4QueueDiscItem> ip = DynamicCast<Ipv4QueueDiscItem>(item);
    if (ip)
    {
        uint8_t proto = ip->GetHeader().GetProtocol();
        uint16_t src = 0;
        uint16_t dst = 0;
        if (proto == 17)
        {
            UdpHeader h;
            item->GetPacket()->PeekHeader(h);
            src = h.GetSourcePort();
            dst = h.GetDestinationPort();
        }
        else if (proto == 6)
        {
            TcpHeader h;
            item->GetPacket()->PeekHeader(h);
            src = h.GetSourcePort();
            dst = h.GetDestinationPort();
        }
        auto it = m_bandOf.find(dst);
        if (it == m_bandOf.end())
        {
            it = m_bandOf.find(src);
        }
        if (it != m_bandOf.end())
        {
            band = it->second;
        }
    }
    return GetQueueDiscClass(band)->GetQueueDisc()->Enqueue(item);
}

void
FlowQueueDisc::Refill()
{
    Time now = Simulator::Now();
    double dt = (now - m_last).GetSeconds();
    for (uint32_t b = 0; b < m_bands.size(); b++)
    {
        if (m_mode == CAP)
        {
            m_tokens[b] = std::min<double>(m_quantum, m_tokens[b] + m_rate[b].GetBitRate() / 8.0 * dt);
        }
        if (m_bands[b].largest.GetBitRate() > 0)
        {
            m_limit[b] = std::min<double>(m_quantum, m_limit[b] + m_bands[b].largest.GetBitRate() / 8.0 * dt);
        }
    }
    m_last = now;
}

// Whether the band's largest rate holds its next packet back now; if so, wait is shortened to when it may go.
bool
FlowQueueDisc::Held(uint32_t b, uint32_t size, Time& wait) const
{
    const DataRate& max = m_bands[b].largest;
    if (max.GetBitRate() == 0 || m_limit[b] >= size)
    {
        return false;
    }
    wait = std::min(wait, max.CalculateBytesTxTime(static_cast<uint32_t>(size - m_limit[b]) + 1));
    return true;
}

void
FlowQueueDisc::Sent(uint32_t b, uint32_t size)
{
    if (m_bands[b].largest.GetBitRate() > 0)
    {
        m_limit[b] -= size;
    }
}

void
FlowQueueDisc::WakeAfter(Time wait)
{
    if (wait != Time::Max() && m_wake.IsExpired())
    {
        m_wake = Simulator::Schedule(wait, &QueueDisc::Run, this);
    }
}

Ptr<QueueDiscItem>
FlowQueueDisc::DoDequeue()
{
    const uint32_t n = m_bands.size();
    // everything else (acknowledgements, ARP) goes first: it is little, and holding it would stall the flows
    Ptr<QueueDisc> other = GetQueueDiscClass(n)->GetQueueDisc();
    if (other->GetNPackets() > 0)
    {
        return other->Dequeue();
    }
    Refill();
    Time wait = Time::Max();
    std::vector<bool> ready(n);
    bool any = false;
    for (uint32_t b = 0; b < n; b++)
    {
        Ptr<QueueDisc> q = GetQueueDiscClass(b)->GetQueueDisc();
        ready[b] = q->GetNPackets() > 0 && !Held(b, q->Peek()->GetSize(), wait);
        any = any || ready[b];
    }
    if (m_mode == CAP)
    {
        for (uint32_t k = 0; k < n; k++)
        {
            uint32_t b = (m_cur + k) % n;
            if (!ready[b])
            {
                continue;
            }
            Ptr<QueueDisc> q = GetQueueDiscClass(b)->GetQueueDisc();
            uint32_t size = q->Peek()->GetSize();
            if (m_tokens[b] >= size)
            {
                m_tokens[b] -= size;
                m_cur = (b + 1) % n;
                Sent(b, size);
                return q->Dequeue();
            }
            wait = std::min(wait, m_rate[b].CalculateBytesTxTime(static_cast<uint32_t>(size - m_tokens[b]) + 1));
        }
        WakeAfter(wait);
        return nullptr;
    }
    if (m_mode == PRIO)
    {
        for (uint32_t b = 0; b < n; b++)
        {
            if (ready[b])
            {
                Ptr<QueueDisc> q = GetQueueDiscClass(b)->GetQueueDisc();
                Sent(b, q->Peek()->GetSize());
                return q->Dequeue();
            }
        }
        WakeAfter(wait);
        return nullptr;
    }
    // share: deficit round robin; a band that is empty, or held by its largest rate, is passed over
    while (any)
    {
        if (!ready[m_cur])
        {
            m_deficit[m_cur] = 0;
            m_cur = (m_cur + 1) % n;
            continue;
        }
        Ptr<QueueDisc> q = GetQueueDiscClass(m_cur)->GetQueueDisc();
        int64_t size = q->Peek()->GetSize();
        if (m_deficit[m_cur] < size)
        {
            m_deficit[m_cur] += static_cast<int64_t>(m_quantum * m_w[m_cur] * n / 2.0);
            m_cur = (m_cur + 1) % n;
            continue;
        }
        Ptr<QueueDiscItem> item = q->Dequeue();
        m_deficit[m_cur] -= item->GetSize();
        Sent(m_cur, item->GetSize());
        return item;
    }
    WakeAfter(wait);
    return nullptr;
}

bool
FlowQueueDisc::CheckConfig()
{
    if (GetNInternalQueues() > 0 || GetNPacketFilters() > 0)
    {
        return false;
    }
    return !m_bands.empty() && GetNQueueDiscClasses() == m_bands.size() + 1;
}

void
FlowQueueDisc::InitializeParams()
{
    const uint32_t n = m_bands.size();
    Ptr<NetDeviceQueueInterface> ndqi = GetNetDeviceQueueInterface();
    Ptr<NetDevice> dev = ndqi ? ndqi->GetObject<NetDevice>() : nullptr;
    NS_ABORT_MSG_IF(!dev, "FlowQueueDisc must be the root queue disc of a device");
    DataRateValue rate;
    dev->GetAttribute("DataRate", rate);
    m_linkRate = rate.Get();
    m_deficit.assign(n, 0);
    m_tokens.assign(n, m_quantum);
    m_limit.assign(n, m_quantum);
    m_rate.clear();
    for (uint32_t b = 0; b < n; b++)
    {
        m_rate.push_back(DataRate(static_cast<uint64_t>(m_w[b] * m_linkRate.GetBitRate())));
    }
    m_cur = 0;
    m_last = Simulator::Now();
}

} // namespace ns3
