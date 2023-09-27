import psycopg2
import configuration

postgres_config = configuration.PostgresConfig()
conn = psycopg2.connect(**postgres_config.config)
