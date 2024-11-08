Init command:  
docker-compose up --build -d  
docker-compose run web python manage.py migrate (數據庫遷移)  
連線至localhost/verifier or localhost/signature
  
Open docker cmd:  
docker-compose exec web /bin/bash  