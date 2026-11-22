#ifndef FLOW_QUEUE_DISC_H
#define FLOW_QUEUE_DISC_H

#include "ns3/data-rate.h"
#include "ns3/event-id.h"
#include "ns3/nstime.h"
#include "ns3/queue-disc.h"

#include <map>
#include <vector>

namespace ns3
{

// The scheduler of the program `net`: one band per flow that passes it, in the order given, and one more band
// (the last) for everything else (acknowledgements of flows that pass the other way, ARP), which is always served
// first. A band has a part of the link and, optionally, a largest rate.
// How the bands share the link is the operator's choice and comes from the environment variable TWOHOSTS_SCHED:
//   share  deficit round robin by the parts: what one band leaves unused goes to the others
//   cap    each band is held to its part of the link's rate, whatever the others send
//   prio   the first band of the list that has a packet goes first; the parts are not used
// LinkQueueDisc of the program `two-hosts` is this with exactly two bands; that program is not changed.
class FlowQueueDisc : public QueueDisc
{
  public:
    enum Mode
    {
        SHARE,
        CAP,
        PRIO
    };
    struct Band
    {
        std::vector<uint16_t> ports; // packets to or from one of these ports belong to the band (one flow, or several that share the queue)
        double part;      // its part of the link, above 0 (the parts are divided by their sum)
        DataRate largest; // 0: no largest rate
    };
    static TypeId GetTypeId();
    FlowQueueDisc();
    ~FlowQueueDisc() override;
    void SetBands(const std::vector<Band>& bands); // before the simulation starts; children = bands + 1

  private:
    bool DoEnqueue(Ptr<QueueDiscItem> item) override;
    Ptr<QueueDiscItem> DoDequeue() override;
    bool CheckConfig() override;
    void InitializeParams() override;
    void Refill();
    bool Held(uint32_t b, uint32_t size, Time& wait) const;
    void Sent(uint32_t b, uint32_t size);
    void WakeAfter(Time wait);

    uint32_t m_quantum;
    Mode m_mode;
    std::vector<Band> m_bands;
    std::map<uint16_t, uint32_t> m_bandOf; // port -> band
    std::vector<double> m_w;               // the parts divided by their sum
    DataRate m_linkRate;
    std::vector<int64_t> m_deficit;
    uint32_t m_cur;
    std::vector<DataRate> m_rate;  // cap: part of the link's rate
    std::vector<double> m_tokens;  // cap: bytes the band may still send
    std::vector<double> m_limit;   // bytes the band may still send under its largest rate
    Time m_last;
    EventId m_wake;
};

} // namespace ns3
#endif
