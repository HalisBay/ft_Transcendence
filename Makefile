.PHONY: up down clean fclean status

up:
	@if [ ! -f docker/up_env.sh ]; then echo "Error: up_env.sh not found!"; exit 1; fi
	@echo "Setting up HOSTIP..."
	cd docker && ./up_env.sh
	@echo "Building and starting containers..."
	cd docker && docker-compose up --build
down:
	@echo "...Stopping containers..."
	cd docker && docker-compose down
clean:
	@echo "...Cleaning up unused images and containers..."
	docker system prune -f
fclean:
	@echo "...Cleaning up all images and containers..."
	docker system prune  -f
status:
	@echo "...Container status..."
	docker ps -a