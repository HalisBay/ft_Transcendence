.PHONY: up down clean status restart build


up:
	@if [ ! -f docker/up_env.sh ]; then echo "Error: up_env.sh not found!"; exit 1; fi
	@echo "Setting up HOSTIP..."
	cd docker && ./up_env.sh
	@echo "Building and starting containers..."
	cd docker && docker-compose up --build


down:
	@echo "...Stopping containers..."
	cd docker && docker-compose down


clean:	down
	@echo "...Cleaning up unused images, containers, volumes, and networks..."
	docker system prune -af
	docker volume prune -af
	docker network prune -f


status:
	@echo "...Container status..."
	cd docker && docker-compose ps


build:
	@echo "Building images only..."
	cd docker && docker-compose build


restart: down up