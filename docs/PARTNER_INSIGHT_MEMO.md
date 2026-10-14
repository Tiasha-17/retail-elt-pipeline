# Partner performance insight memo

## Decision

Use a two-track partner programme: protect the highest-value sellers while routing
partners with repeated delivery or customer-experience issues into an operational
improvement queue. Do not rank partners on revenue alone.

## Evidence from the full public Olist dataset

A reference run over the complete marketplace history produced:

- **3,095 partners** and **100,010 seller-order relationships**.
- **$13.59m item revenue**, with an average **$135.90** per seller-order.
- The highest-revenue **10% of partners generated 67.56% of item revenue**.
- **8.02% of delivered seller-orders were late**.
- Average review score was **2.57 for late deliveries** versus **4.27 for
  on-time deliveries**.
- Cancellation or unavailable status affected **0.47% of seller-orders**.

The strongest actionable relationship is delivery reliability and customer
experience. The concentration result matters too: a small strategic-partner group
deserves proactive monitoring because disruption there can affect a large share of
marketplace value.

## Recommended actions

1. **Create a weekly at-risk queue.** Prioritise partners with enough volume to be
   reliable and with late-delivery, cancellation or low-review performance worse
   than portfolio benchmarks.
2. **Protect strategic partners.** Monitor revenue concentration alongside service
   measures so high-value partners receive early intervention before performance
   deterioration becomes material.
3. **Test the intervention.** Track whether partners entering the improvement queue
   reduce late-delivery and low-review rates over the following 30 and 60 days.
   Compare against similar partners not yet contacted; do not claim impact from a
   before-and-after chart alone.

## Limitations

- The source is a historical public marketplace dataset, not live operational data.
- Item revenue is gross merchandise value, not margin, commission or recognised
  company revenue.
- Reviews are recorded at order level and therefore shared across sellers when an
  order has multiple partners.
- The source lacks carrier, route, fulfilment-centre and intervention data, so this
  analysis identifies where to investigate but cannot establish why a delivery was
  late or whether an intervention caused improvement.
- The segmentation is a prioritisation aid. It should not be used for automated
  partner penalties.

The reference figures were independently reconciled against the companion Olist
star schema used by the retail NL2SQL project. The dbt analytics models in this
repository reproduce the same definitions from the ELT warehouse.
