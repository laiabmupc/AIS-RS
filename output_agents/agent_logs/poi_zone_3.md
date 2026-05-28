# Barcelona POI database curator

## Prompt

You are the agent: Barcelona POI database curator.
Goal: Create realistic structured POI records for a sustainable tourism recommender simulation.
Follow the task exactly. Be concise. Do not invent explanations outside the requested format.

Task:
Create exactly 10 distinct Barcelona POIs for this zone: Montjuic and port area.
The neighbourhood value must be exactly one of these names, never a number: Montjuic, Poble Sec, Hostafrancs, Port Vell, Sants.
Useful real-place hints for this zone: MNAC, Montjuic Castle, Fundacio Joan Miro, Poble Espanyol, Magic Fountain, CaixaForum, Olympic Stadium, Joan Miro Foundation gardens, Hostafrancs Market, Port Vell promenade.
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
      "n": "MNAC",
      "neighbourhood": "Montjuic",
      "lat": 41.3928,
      "lon": 2.1675,
      "cats": "architecture,museum,local",
      "pop": 0.85,
      "cap": 1000,
      "cost": 10,
      "outdoor": 0.9,
      "culture": 0.7,
      "local_economy": 0.6,
      "green": 0.4
    },
    {
      "n": "Fundacio Joan Miro",
      "neighbourhood": "Montjuic",
      "lat": 41.3928,
      "lon": 2.1675,
      "cats": "art,local",
      "pop": 0.8,
      "cap": 200,
      "cost": 10,
      "outdoor": 0.9,
      "culture": 0.8,
      "local_economy": 0.7,
      "green": 0.3
    },
    {
      "n": "Poble Espanyol",
      "neighbourhood": "Montjuic",
      "lat": 41.3928,
      "lon": 2.1675,
      "cats": "architecture,museum,local",
      "pop": 0.75,
      "cap": 500,
      "cost": 10,
      "outdoor": 0.9,
      "culture": 0.8,
      "local_economy": 0.6,
      "green": 0.4
    },
    {
      "n": "Magic Fountain",
      "neighbourhood": "Montjuic",
      "lat": 41.3928,
      "lon": 2.1675,
      "cats": "viewpoint,art,museum",
      "pop": 0.8,
      "cap": 200,
      "cost": 10,
      "outdoor": 0.9,
      "culture": 0.7,
      "local_economy": 0.5,
      "green": 0.3
    },
    {
      "n": "CaixaForum",
      "neighbourhood": "Montjuic",
      "lat": 41.3928,
      "lon": 2.1675,
      "cats": "architecture,museum,local",
      "pop": 0.7,
      "cap": 300,
      "cost": 10,
      "outdoor": 0.9,
      "culture": 0.8,
      "local_economy": 0.6,
      "green": 0.4
    },
    {
      "n": "Olympic Stadium",
      "neighbourhood": "Montjuic",
      "lat": 41.3928,
      "lon": 2.1675,
      "cats": "architecture,museum,local",
      "pop": 0.7,
      "cap": 500,
      "cost": 10,
      "outdoor": 0.9,
      "culture": 0.8,
      "local_economy": 0.6,
      "green": 0.4
    },
    {
      "n": "Joan Miro Foundation gardens",
      "neighbourhood": "Montjuic",
      "lat": 41.3928,
      "lon": 2.1675,
      "cats": "park,art,museum",
      "pop": 0.8,
      "cap": 300,
      "cost": 10,
      "outdoor": 0.9,
      "culture": 0.8,
      "local_economy": 0.7,
      "green": 0.5
    },
    {
      "n": "Hostafrancs Market",
      "neighbourhood": "Montjuic",
      "lat": 41.3928,
      "lon": 2.1675,
      "cats": "market,local",
      "pop": 0.7,
      "cap": 200,
      "cost": 10,
      "outdoor": 0.9,
      "culture": 0.4,
      "local_economy": 0.8,
      "green": 0.3
    },
    {
      "n": "Port Vell promenade",
      "neighbourhood": "Port Vell",
      "lat": 41.3928,
      "lon": 2.1675,
      "cats": "viewpoint,beach,museum",
      "pop": 0.8,
      "cap": 500,
      "cost": 10,
      "outdoor": 0.9,
      "culture": 0.7,
      "local_economy": 0.6,
      "green": 0.4
    },
    {
      "n": "Poble Sec",
      "neighbourhood": "Poble Sec",
      "lat": 41.3895,
      "lon": 2.1704,
      "cats": "architecture,local",
      "pop": 0.6,
      "cap": 300,
      "cost": 10,
      "outdoor": 0.8,
      "culture": 0.5,
      "local_economy": 0.7,
      "green": 0.4
    }
  ]
}
