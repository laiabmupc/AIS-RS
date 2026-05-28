# Barcelona POI database curator

## Prompt

You are the agent: Barcelona POI database curator.
Goal: Create realistic structured POI records for a sustainable tourism recommender simulation.
Follow the task exactly. Be concise. Do not invent explanations outside the requested format.

Task:
Create exactly 10 distinct Barcelona POIs for this zone: Western and mountain areas.
The neighbourhood value must be exactly one of these names, never a number: Les Corts, Sarria, Pedralbes, Sant Gervasi, Collserola.
Useful real-place hints for this zone: Camp Nou Museum, Pedralbes Monastery, Pedralbes Gardens, Torre Bellesguard, Sarria old town, CosmoCaixa, Carretera de les Aigues, Collserola viewpoints, Monastery gardens, Sant Gervasi market area.
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
      "n": "Camp Nou Museum",
      "neighbourhood": "Sarria",
      "lat": 41.3862,
      "lon": 2.1795,
      "cats": "museum,local",
      "pop": 0.8,
      "cap": 300,
      "cost": 10,
      "outdoor": 0.2,
      "culture": 0.6,
      "local_economy": 0.75,
      "green": 0.4
    },
    {
      "n": "Torre Bellesguard",
      "neighbourhood": "Pedralbes",
      "lat": 41.3928,
      "lon": 2.1696,
      "cats": "architecture,local",
      "pop": 0.75,
      "cap": 450,
      "cost": 15,
      "outdoor": 0.8,
      "culture": 0.8,
      "local_economy": 0.9,
      "green": 0.6
    },
    {
      "n": "Collserola viewpoints",
      "neighbourhood": "Collserola",
      "lat": 41.3752,
      "lon": 2.1837,
      "cats": "viewpoint,local",
      "pop": 0.6,
      "cap": 900,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.4,
      "local_economy": 1,
      "green": 0.7
    },
    {
      "n": "Sarria old town",
      "neighbourhood": "Sarria",
      "lat": 41.3856,
      "lon": 2.1795,
      "cats": "market,local",
      "pop": 0.7,
      "cap": 700,
      "cost": 0,
      "outdoor": 0.8,
      "culture": 0.3,
      "local_economy": 1,
      "green": 0.5
    },
    {
      "n": "Pedralbes Monastery",
      "neighbourhood": "Pedralbes",
      "lat": 41.3928,
      "lon": 2.1696,
      "cats": "religious,local",
      "pop": 0.75,
      "cap": 300,
      "cost": 10,
      "outdoor": 0.2,
      "culture": 0.4,
      "local_economy": 0.9,
      "green": 0.6
    },
    {
      "n": "CosmoCaixa",
      "neighbourhood": "Collserola",
      "lat": 41.3752,
      "lon": 2.1837,
      "cats": "science,local",
      "pop": 0.6,
      "cap": 900,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.5,
      "local_economy": 1,
      "green": 0.7
    },
    {
      "n": "Carretera de les Aigues",
      "neighbourhood": "Collserola",
      "lat": 41.3752,
      "lon": 2.1837,
      "cats": "beach,local",
      "pop": 0.6,
      "cap": 900,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.4,
      "local_economy": 1,
      "green": 0.7
    },
    {
      "n": "Monastery gardens",
      "neighbourhood": "Sant Gervasi",
      "lat": 41.3862,
      "lon": 2.1795,
      "cats": "park,local",
      "pop": 0.75,
      "cap": 700,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.3,
      "local_economy": 1,
      "green": 0.8
    },
    {
      "n": "Pedralbes Gardens",
      "neighbourhood": "Pedralbes",
      "lat": 41.3928,
      "lon": 2.1696,
      "cats": "park,local",
      "pop": 0.75,
      "cap": 700,
      "cost": 0,
      "outdoor": 0.9,
      "culture": 0.3,
      "local_economy": 1,
      "green": 0.8
    },
    {
      "n": "Sant Gervasi market area",
      "neighbourhood": "Sant Gervasi",
      "lat": 41.3862,
      "lon": 2.1795,
      "cats": "market,local",
      "pop": 0.75,
      "cap": 700,
      "cost": 0,
      "outdoor": 0.8,
      "culture": 0.3,
      "local_economy": 1,
      "green": 0.6
    }
  ]
}
