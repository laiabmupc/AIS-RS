# Barcelona POI database curator

## Prompt

You are the agent: Barcelona POI database curator.
Goal: Create realistic structured POI records for a sustainable tourism recommender simulation.
Follow the task exactly. Be concise. Do not invent explanations outside the requested format.

Task:
Create exactly 10 distinct Barcelona POIs for this zone: Eastern innovation and beach areas.
The neighbourhood value must be exactly one of these names, never a number: Poblenou, Glories, Diagonal Mar, Sant Marti, Sant Andreu, El Clot.
Useful real-place hints for this zone: Glories Tower, Design Museum, Mercat dels Encants, Rambla del Poblenou, Bogatell Beach, Forum Park, Natural Science Museum, Fabra i Coats, Sant Andreu old town, Clot Park.
POI names should be actual attractions, parks, museums, markets, streets, churches or viewpoints, not generic numbered items.
Do not repeat any POI name inside the answer. Do not put Sagrada Familia or Casa Batllo outside the Eixample/Sagrada Familia zone.
Use only these category tags, comma separated: architecture, religious, museum, park, market, food, beach, viewpoint, shopping, nightlife, family, science, local.
Use plausible Barcelona coordinates. Numeric scores must be between 0 and 1, except capacity and cost.
Popularity should reflect expected tourist fame, not personal preference. Include famous and less famous places.
Use varied numeric values. Do not copy the same scores for every POI.
Outdoor guidance: parks, beaches, viewpoints and streets should have outdoor above 0.75; indoor museums and churches below 0.35.
Cost guidance: streets, parks, beaches and markets can be 0; museums usually 6-20; iconic paid monuments 15-35.
Capacity guidance: small museums/churches 150-450; big parks/beaches/streets 700-1500; markets/monuments 300-900.
Use the compact keys from the schema to keep the answer short.
Return only valid JSON with this schema:
{"pois": [{"n": "POI name", "neighbourhood": "one allowed neighbourhood", "lat": "float", "lon": "float", "cats": "comma tags", "pop": "0-1", "cap": "integer", "cost": "euros", "outdoor": "0-1", "culture": "0-1", "local_economy": "0-1", "green": "0-1"}]}

## Answer

{
  "pois": [
    {
      "n": "Glories Tower",
      "neighbourhood": "Glories",
      "lat": 41.3862,
      "lon": 2.1795,
      "cats": "viewpoint,architecture,museum",
      "pop": 0.85,
      "cap": 700,
      "cost": 10,
      "outdoor": 0.9,
      "culture": 0.6,
      "local_economy": 0.4,
      "green": 0.3
    },
    {
      "n": "Design Museum",
      "neighbourhood": "Diagonal Mar",
      "lat": 41.3875,
      "lon": 2.1695,
      "cats": "museum,architecture",
      "pop": 0.75,
      "cap": 450,
      "cost": 15,
      "outdoor": 0.3,
      "culture": 0.8,
      "local_economy": 0.2,
      "green": 0.6
    },
    {
      "n": "Mercat dels Encants",
      "neighbourhood": "Poblenou",
      "lat": 41.3957,
      "lon": 2.1833,
      "cats": "market,local",
      "pop": 0.65,
      "cap": 900,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.4,
      "local_economy": 1,
      "green": 0.7
    },
    {
      "n": "Rambla del Poblenou",
      "neighbourhood": "Poblenou",
      "lat": 41.3952,
      "lon": 2.1867,
      "cats": "viewpoint,shopping,streets",
      "pop": 0.8,
      "cap": 1500,
      "cost": 0,
      "outdoor": 0.95,
      "culture": 0.3,
      "local_economy": 0.7,
      "green": 0.2
    },
    {
      "n": "Bogatell Beach",
      "neighbourhood": "Diagonal Mar",
      "lat": 41.3865,
      "lon": 2.1695,
      "cats": "beach,local",
      "pop": 0.7,
      "cap": 700,
      "cost": 0,
      "outdoor": 0.95,
      "culture": 0.3,
      "local_economy": 1,
      "green": 0.8
    },
    {
      "n": "Forum Park",
      "neighbourhood": "Sant Marti",
      "lat": 41.3762,
      "lon": 2.1595,
      "cats": "park,local",
      "pop": 0.8,
      "cap": 700,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.4,
      "local_economy": 1,
      "green": 0.6
    },
    {
      "n": "Natural Science Museum",
      "neighbourhood": "Sant Marti",
      "lat": 41.3758,
      "lon": 2.1595,
      "cats": "museum,science",
      "pop": 0.6,
      "cap": 450,
      "cost": 10,
      "outdoor": 0.3,
      "culture": 0.8,
      "local_economy": 0.2,
      "green": 0.7
    },
    {
      "n": "Fabra i Coats",
      "neighbourhood": "Sant Andreu",
      "lat": 41.3956,
      "lon": 2.1833,
      "cats": "architecture,local",
      "pop": 0.7,
      "cap": 450,
      "cost": 10,
      "outdoor": 0.3,
      "culture": 0.6,
      "local_economy": 1,
      "green": 0.8
    },
    {
      "n": "Sant Andreu old town",
      "neighbourhood": "Sant Andreu",
      "lat": 41.3952,
      "lon": 2.1867,
      "cats": "local,viewpoint",
      "pop": 0.8,
      "cap": 700,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.3,
      "local_economy": 1,
      "green": 0.5
    },
    {
      "n": "Clot Park",
      "neighbourhood": "El Clot",
      "lat": 41.3862,
      "lon": 2.1795,
      "cats": "park,local",
      "pop": 0.7,
      "cap": 700,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.4,
      "local_economy": 1,
      "green": 0.8
    }
  ]
}
