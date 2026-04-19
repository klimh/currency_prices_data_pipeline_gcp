# NBP Currency Data Pipeline 

To jest jeden z moich projektów do portfolio, w którym uczyłem się w praktyce pracy z Google Cloud Platform (GCP) i narzędzi z kategorii Infrastructure as Code (IaC).  
Zbudowałem tu prosty, ale kompletny potok danych (data pipeline), który codziennie automatycznie pobiera kursy walut z API Narodowego Banku Polskiego i przygotowuje je do analityki w chmurze.

## Co robi ten projekt?
Głównym celem jest regularne zasilanie bazy spójnymi danymi finansowymi bez mojej ingerencji. 
Aplikacja odpytuje publiczne API NBP o tabelę kursów średnich, a następnie ładuje wyciągnięte informacje do cloudowego storage'u jako pliki JSON (prosty data lake). Na koniec wszystko jest spięte z hurtownią danych Google BigQuery, co pozwala mi od razu wyciągać informacje za pomocą zwykłych zapytań SQL.

Oprócz potoku danych, aplikacja wystawia również API z analitycznymi endpointami:
* `/analyze` - obrazuje podejście Data Engineering. Odpytuje bezpośrednio hurtownię BigQuery, parsuje zagnieżdżone struktury (`UNNEST`) i zwraca 5 walut o najwyższym kursie.
* `/ask` - implementacja **AI Asystenta we wzorcu RAG** (Retrieval-Augmented Generation)! Wykorzystuje model **Gemini 1.5 Flash**. Aplikacja wyciąga dzisiejsze kursy walut z BigQuery, buduje z nich kontekst i wysyła do modelu AI, dzięki czemu można mu zadawać pytania w języku naturalnym (np. "Jakie waluty mają kurs powyżej 4 PLN?").

## Architektura i narzędzia 
Całość infrastruktury napisałem w **Terraformie** (`main.tf`), żeby uniknąć wyklikiwania usług krok po kroku w konsoli(chociaż tak też czasami lubię robić). Dzięki temu mogłem też łatwo psuć i stawiać wszystko od nowa w trakcie dewelopmentu.

Oto czego dokładnie użyłem:
* **Python (FastAPI, Pandas)** - główny silnik do integracji z użyciem lekkiego frameworka.
* **Docker** - środowisko pracy zamknięte w kontenerze (deploy leci do Artifact Registry wbudowanego w GCP).
* **Terraform** - powoływanie zasobów, nadawanie odpowiednich ról i wiązanie klocków ze sobą (IaC).
* **Google Cloud Run (Serverless)** - tutaj hostuje się mój kod. Usługa włącza się tylko wtedy, kiedy dostaje żądanie, więc jest bardzo tania (prawie darmowa przy takich obciążeniach).
* **Google Cloud Scheduler** - taki chmurowy "cron". Skonfigurowany tak, by co rano o 9:00 uderzał w moją apkę na Cloud Runie.
* **Google Cloud Storage (GCS)** - pełni tu rolę tzw. "Data Lake". Wpada tu każdy dzienny zrzut walut w formacie JSONL (newline-delimited JSON!!). Bucket ma ustawioną regułę lifecycle na kasowanie starych plików.
* **Google BigQuery** - baza odpytująca bezpośrednio pliki JSON z mojego builda na GCSie (external table). Dla mnie to jak prawdziwy SQL tylko czytający prosto z plików.
* **Generative AI (Gemini / Vertex AI)** - to już nie tylko plany! Zaimplementowałem wzorzec **RAG**, który łączy bazę danych (BigQuery) z najnowszym modelem językowym Gemini. Terraform również zarządza połączeniami do AI (nadaje role dla Vertex AI).

## Jak to uruchomić u siebie?
Jeśli ktoś chciałby postawić dokładną kopię mojej architektury:
1. Zmieniamy zmienną `project_id` w pliku `variables.tf` na ID własnego projektu w Google Cloud.
2. Budujemy Dockerfile i pchamy zbudowany obraz kontenera do utworzonego Artifact Registry.
3. Wdrażamy całość poleceniami:
   ```bash
   terraform init
   terraform apply
   ```
   (też używam terraform plan żeby sprawdzić co się zmieni przed apply więc polecam)

Magia IaC - za parę chwil wszystko śmiga. Po testach na koncie chmurowym wystarczy sprawnie posprzątać przy użyciu `terraform destroy` i po problemie, chociaż koszty są tak małe że można nawet o tym zapomnieć.

## Małe podsumowanie
Fajna nauka. Wbrew pozorom postawienie tego w chmurze to jedno, ale największym wyzwaniem i najlepszą lekcją było wymyślanie jak poprawnie przydzielić dostępy IAM przez kod w TF – musisz zadbać, żeby Cloud Run mógł zapisać do Storage, Scheduler odpalić apkę na publicznym endpointcie, a BigQuery mieć prawa połączenia z Vertexem. Przygotowałem to w formie, którą będę po prostu rozwijać jako mój mały poligon do testowania usług Google w praktyce.
