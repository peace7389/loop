#ifndef WRR_QUEUE_DISC_H
#define WRR_QUEUE_DISC_H

#include "ns3/data-rate.h"
#include "ns3/event-id.h"
#include "ns3/nstime.h"
#include "ns3/queue-disc.h"

namespace ns3
{

// Two-band scheduler: band 0 = socket priority 6 (UDP here), band 1 = everything else.
class WrrQueueDisc : public QueueDisc
{
  public:
    enum Mode
    {
        SHARE,
        CAP
    };
    static TypeId GetTypeId();
    WrrQueueDisc();
    ~WrrQueueDisc() override;

  private:
    bool DoEnqueue(Ptr<QueueDiscItem> item) override;
    Ptr<QueueDiscItem> DoDequeue() override;
    bool CheckConfig() override;
    void InitializeParams() override;
    void Refill();

    double m_weightUdp;
    uint32_t m_quantum;
    Mode m_mode;
    DataRate m_linkRate;
    int64_t m_deficit[2];
    uint32_t m_cur;
    DataRate m_rate[2];
    double m_tokens[2];
    Time m_lastRefill;
    EventId m_wake;
};

} // namespace ns3
#endif
