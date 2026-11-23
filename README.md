# Poultry Farm Data Engineering Platform
Developed a Python=based data engineering platform designed to collect, clean, transform, and analyse poultry farm production data. The system processes daily flock records, including bird population, mortality, feed consumption, water consumption, and average body weight, to generate actionable production insights.


## Business problem
Farm managers need reliable daily visibility into flock size, mortality, feed use, water use, average body weight, and feed conversion.

## Pipeline
CSV ingestion → schema/type cleaning → validation → KPI calculations → curated CSV + SQLite.

## Key metrics
- Mortality rate (%) = daily deaths / opening birds × 100
- Average weight (kg) = total sampled live weight / sampled birds
- Feed conversion ratio (FCR) = cumulative feed consumed (kg) / estimated liveweight gain (kg)
- Water-to-feed ratio = water consumed (L) / feed consumed (kg)

FCR is calculated cumulatively by flock. The demonstration dataset uses a simplified liveweight-gain estimate; real deployments should account for placement weight, removals, transfers, and flock-specific measurement protocols.
