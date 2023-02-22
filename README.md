# Regen
![Test](https://github.com/glinerosuarez/regen/actions/workflows/pull-request.yml/badge.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Regen is a toolbox to build and deploy trading agents that work on 
environments that follow [Farama's Env](https://gymnasium.farama.org/api/env/)
interface.

## Project Focus

The purpose of this project is to provide all the architecture components
neccessary to build a trading application end-to-end, that is, ELT pipelines
to get data for environments, which includes the historical data for training
agents and backtesting as well as the live data for deployments, environments
which are the interfaces to for agents to trade assets and agents that define
the policies to execute.

## Requirements
|            | Version                | 
|------------|------------------------|
| Terraform  | 1.3.7                  | 
| Docker     | 20.10.22               |

## ELT
All the ELT infrastructure is defined as Terraform code inside the directory
`infra`

![img.png](img.png)

The ELT pipeline is orchestrated using [Airflow](https://github.com/apache/airflow),
the extraction layer comprises python tasks that get data from sources
in batches and load it on a Postgres database that serves as the data warehouse,
once there, data transformations are performed as [dbt](https://www.getdbt.com/) modules
to compute the observations table that is consumed by the environment. At the moment 
there is a single pipeline that produces the observations table for the single 
crypto-asset environment.


This a work in progress, at the moment 

## Environments
Environments are interfaces to expose data that agents need to make decisions, 
additionally, they execute actions the agents make at a specified step, episode and 
execution. they are subclasses of [Farama's Env](https://gymnasium.farama.org/api/env/).
At the moment there is a single environment available, which is the single crypto-asset
environment.

### Single crypto-asset environment
An environment that provides data about a specific cryptocurrency asset at a given minute,
an observation is made up of 11 features: open value, highest value, lowest value, 
close value, and 7 moving averages data points (with 7, 25, 100, 300, 1440, 
14400, 144000 window sizes) in the last minute.

## Agents
Agents choose actions in an environment. At the moment only the deep 
reinforcement learning agent is available.

### Deep Reinforcement Learning Agent
An agent that relies on deep reinforcement learning algorithms to build
policies. [stable-baselines3](https://stable-baselines3.readthedocs.io/en/master/)
implementations are used.

## Getting Started
### Set up infrastructure
1. go to the infra folder `cd infra`
2. run `terraform apply` to deploy infrastructure
### Train
#### Single crypto-asset
1. Trigger the `klines_backfill`, `ma_backfill` and `dbt_run` DAG's in 
sequence that should be available in the Airflow server in
`http://localhost:8080/` to put historical data in the observations table in
the database that is hosted by the `regen_db` container.
2. Run `docker exec agent python main.py -t` to train the agent.

### Run in live mode

### Parameters
