#include "wrr-queue-disc.h"

#include "ns3/double.h"
#include "ns3/enum.h"
#include "ns3/log.h"
#include "ns3/object-factory.h"
#include "ns3/simulator.h"
#include "ns3/socket.h"
#include "ns3/uinteger.h"

namespace ns3
{

NS_LOG_COMPONENT_DEFINE("WrrQueueDisc");
NS_OBJECT_ENSURE_REGISTERED(WrrQueueDisc);

TypeId
WrrQueueDisc::GetTypeId()
{
    static TypeId tid =
        TypeId("ns3::WrrQueueDisc")
            .SetParent<QueueDisc>()
            .SetGroupName("TrafficControl")
            .AddConstructor<WrrQueueDisc>()
            .AddAttribute("WeightUdp", "Share of the link configured for band 0",
                          DoubleValue(0.5), MakeDoubleAccessor(&WrrQueueDisc::m_weightUdp),
                          MakeDoubleChecker<double>(0.05, 0.95))
            .AddAttribute("Quantum", "Bytes added to a band's deficit per visit (share), burst (cap)",
                          UintegerValue(3000), MakeUintegerAccessor(&WrrQueueDisc::m_quantum),
                          MakeUintegerChecker<uint32_t>(1))
            .AddAttribute("Mode", "share or cap", EnumValue(SHARE),
                          MakeEnumAccessor<Mode>(&WrrQueueDisc::m_mode),
                          MakeEnumChecker(SHARE, "share", CAP, "cap"))
            .AddAttribute("LinkRate", "Rate of the link this queue disc feeds",
                          DataRateValue(DataRate("1Gbps")),
                          MakeDataRateAccessor(&WrrQueueDisc::m_linkRate), MakeDataRateChecker());
    return tid;
}

WrrQueueDisc::WrrQueueDisc()
    : QueueDisc(QueueDiscSizePolicy::NO_LIMITS)
{
}

WrrQueueDisc::~WrrQueueDisc()
{
}

bool
WrrQueueDisc::DoEnqueue(Ptr<QueueDiscItem> item)
{
    SocketPriorityTag tag;
    uint8_t prio = item->GetPacket()->PeekPacketTag(tag) ? (tag.GetPriority() & 0x0f) : 0;
    uint32_t band = (prio == 6) ? 0 : 1;
    return GetQueueDiscClass(band)->GetQueueDisc()->Enqueue(item);
}

void
WrrQueueDisc::Refill()
{
    Time now = Simulator::Now();
    double dt = (now - m_lastRefill).GetSeconds();
    for (int b = 0; b < 2; b++)
    {
        m_tokens[b] = std::min<double>(m_quantum, m_tokens[b] + m_rate[b].GetBitRate() / 8.0 * dt);
    }
    m_lastRefill = now;
}

Ptr<QueueDiscItem>
WrrQueueDisc::DoDequeue()
{
    Ptr<QueueDisc> q[2] = {GetQueueDiscClass(0)->GetQueueDisc(), GetQueueDiscClass(1)->GetQueueDisc()};
    if (m_mode == CAP)
    {
        Refill();
        Time wait = Time::Max();
        for (int k = 0; k < 2; k++)
        {
            uint32_t b = (m_cur + k) & 1;
            if (q[b]->GetNPackets() == 0)
            {
                continue;
            }
            uint32_t size = q[b]->Peek()->GetSize();
            if (m_tokens[b] >= size)
            {
                m_tokens[b] -= size;
                m_cur = b ^ 1;
                return q[b]->Dequeue();
            }
            wait = std::min(wait, m_rate[b].CalculateBytesTxTime(static_cast<uint32_t>(size - m_tokens[b]) + 1));
        }
        if (wait != Time::Max() && m_wake.IsExpired())
        {
            m_wake = Simulator::Schedule(wait, &QueueDisc::Run, this);
        }
        return nullptr;
    }
    // share: deficit round robin over the two bands
    const double w[2] = {m_weightUdp, 1.0 - m_weightUdp};
    while (q[0]->GetNPackets() > 0 || q[1]->GetNPackets() > 0)
    {
        if (q[m_cur]->GetNPackets() == 0)
        {
            m_deficit[m_cur] = 0;
            m_cur ^= 1;
            continue;
        }
        int64_t size = q[m_cur]->Peek()->GetSize();
        if (m_deficit[m_cur] < size)
        {
            m_deficit[m_cur] += static_cast<int64_t>(m_quantum * w[m_cur]);
            m_cur ^= 1;
            continue;
        }
        Ptr<QueueDiscItem> item = q[m_cur]->Dequeue();
        m_deficit[m_cur] -= item->GetSize();
        return item;
    }
    return nullptr;
}

bool
WrrQueueDisc::CheckConfig()
{
    if (GetNInternalQueues() > 0 || GetNPacketFilters() > 0)
    {
        return false;
    }
    if (GetNQueueDiscClasses() == 0)
    {
        ObjectFactory factory;
        factory.SetTypeId("ns3::FifoQueueDisc");
        for (int i = 0; i < 2; i++)
        {
            Ptr<QueueDisc> qd = factory.Create<QueueDisc>();
            qd->Initialize();
            Ptr<QueueDiscClass> c = CreateObject<QueueDiscClass>();
            c->SetQueueDisc(qd);
            AddQueueDiscClass(c);
        }
    }
    return GetNQueueDiscClasses() == 2;
}

void
WrrQueueDisc::InitializeParams()
{
    m_deficit[0] = m_deficit[1] = 0;
    m_cur = 0;
    m_rate[0] = DataRate(static_cast<uint64_t>(m_weightUdp * m_linkRate.GetBitRate()));
    m_rate[1] = DataRate(static_cast<uint64_t>((1.0 - m_weightUdp) * m_linkRate.GetBitRate()));
    m_tokens[0] = m_tokens[1] = m_quantum;
    m_lastRefill = Simulator::Now();
}

} // namespace ns3
