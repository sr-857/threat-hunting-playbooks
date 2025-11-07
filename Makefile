.PHONY: demo demo-clean demo-logs

## demo: orchestrate full local demo with seeded hunt execution
 demo:
	@bash ./scripts/demo.sh

## demo-clean: stop containers launched by `make demo`
 demo-clean:
	@docker compose down

## demo-logs: tail docker compose logs
 demo-logs:
	@docker compose logs -f
