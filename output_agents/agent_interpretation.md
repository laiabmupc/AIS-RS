# Verified agent-based interpretation

The popularity baseline concentrates tourists in the most famous and central POIs. It obtains the lowest average satisfaction (0.5970), the highest peak crowding ratio (0.5133), a very high central visit share (0.9072) and the largest top-5 POI concentration (0.6478). This is the expected behaviour of a simple popularity recommender: it is easy to explain, but it reinforces overtourism.

The personalized recommender is the strongest strategy from the individual-user perspective. It reaches the highest satisfaction (0.7036) and the highest simulated Precision@5 (0.9759). However, its city-level behaviour is still less balanced than the sustainable strategy: central visit share remains at 0.4022, hotspot visit share at 0.2566, and top-5 POI share at 0.3532.

The sustainable recommender gives the best urban-management outcome. Compared with popularity, it reduces central visit share by 0.6338, hotspot visit share by 0.7568, and top-5 POI share by 0.3962. It also obtains the highest neighbourhood entropy (0.9707) and the widest POI coverage (0.8772), which means tourists are distributed across more places and neighbourhoods.

The main trade-off is clear and defensible. Sustainable recommendation loses 0.0262 satisfaction points with respect to the personalized recommender, but it remains 0.0804 points above the popularity baseline. Therefore, it does not maximize individual relevance, but it achieves a much better compromise between tourist utility and collective sustainability objectives.

Some indicators need careful interpretation. The popularity strategy has the highest local economy score in this run because several very popular commercial places and markets receive many visits. This does not mean that the wealth is well distributed. The sustainable strategy has a slightly lower average local economy score (0.8217) than popularity (0.8727), but it spreads visits much more widely and increases green visit share to 0.2844, compared with 0.1818 for personalized and 0.0570 for popularity.

Overall, the simulation supports the usefulness of the evaluation mechanism. By comparing the same tourist population under three recommender strategies, it shows that the sustainable approach is superior for reducing overtourism indicators, while the personalized recommender remains best for pure profile relevance.
