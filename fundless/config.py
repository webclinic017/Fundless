from pathlib import Path
import yaml
from typing import List, TypedDict, Union
from pydantic.dataclasses import dataclass
from pydantic.types import confloat, conint, constr
from pydantic import validator
from aenum import MultiValueEnum


# Convention for multi value enums:
#   - value: used in config and code
#   - values[1]: beautiful name for printing
#   - values[2:]: alternative names (might be used by user in config and interaction)
class ExchangeEnum(MultiValueEnum):
    binance = 'binance', 'Binance'
    kraken = 'kraken', 'Kraken'


class BaseCurrencyEnum(MultiValueEnum):
    eur = 'EUR', 'euro', 'Euro', 'eur'
    usd = 'USD', 'usd', 'US Dollar', 'usdollar'
    btc = 'BTC', 'btc', 'Bitcoin', 'bitcoin'
    eth = 'ETH', 'eth', 'Ethereum', 'ethereum', 'ether'


class IntervalEnum(MultiValueEnum):
    daily = 'daily'
    weekly = 'weekly'
    biweekly = 'biweekly', 'bi-weekly'


class OrderTypeEnum(MultiValueEnum):
    market = 'market'
    limit = 'limit'


class WeightingEnum(MultiValueEnum):
    equal = 'equal'
    market_cap = 'marketcap', 'market_cap'
    sqrt_market_cap = 'sqrt_market_cap', 'square root market cap', 'sqrt market cap'
    cbrt_market_cap = 'cbrt_market_cap', 'cubic root market cap', 'cbrt market cap'
    sqrt_sqrt_market_cap = 'sqrt_sqrt_market_cap', 'sqrt sqrt market cap'


class PortfolioModeEnum(MultiValueEnum):
    cherry_pick = 'cherry_pick', 'pick', 'cherry pick', 'Cherry Pick', 'cherry_picked'
    index = 'index', 'Index'


class ExchangeToken(TypedDict):
    api_key: str
    secret: str


class TelegramToken(TypedDict):
    token: str
    chat_id: str


@dataclass
class TradingBotConfig:
    exchange: ExchangeEnum
    test_mode: bool
    base_currency: BaseCurrencyEnum
    base_symbol: constr(strip_whitespace=True, to_lower=True, regex='^(busd|usdc|usdt|usd)$')
    savings_plan_cost: confloat(gt=0, le=10000)
    savings_plan_interval: Union[IntervalEnum, List[conint(ge=1, le=28)]]
    portfolio_mode: PortfolioModeEnum
    portfolio_weighting: WeightingEnum
    cherry_pick_symbols: List[str]
    index_top_n: conint(gt=0, le=100)
    index_exclude_symbols: List[str]

    @validator('base_currency')
    def check_if_currency_supported(cls, v):
        if v in (BaseCurrencyEnum.btc, BaseCurrencyEnum.eth, BaseCurrencyEnum.eur):
            raise NotImplementedError("Only USD base currency is supported by now")
        return v

    @validator('portfolio_mode')
    def check_if_portfolio_supported(cls, v):
        if v in (PortfolioModeEnum.index, ):
            raise NotImplementedError("Only cherry-picked portfolio is supported by now")
        return v

    @classmethod
    def from_config_yaml(cls, file_path):
        file = Path(file_path)
        with open(file) as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                print("Error while parsing config file:")
                print(exc)
                raise exc
        config = data['trading_bot']
        self = cls.from_dict(config)
        return self

    @classmethod
    def from_dict(cls, dictionary):
        self = cls(
            exchange=dictionary['exchange']['selected'],
            test_mode=dictionary['test_mode'],
            base_currency=dictionary['base_currency']['selected'],
            base_symbol=dictionary['base_symbol']['selected'],
            savings_plan_cost=dictionary['savings_plan']['cost'],
            savings_plan_interval=dictionary['savings_plan']['interval']['selected'],
            portfolio_mode=dictionary['portfolio']['mode']['selected'],
            portfolio_weighting=dictionary['portfolio']['weighting']['selected'],
            cherry_pick_symbols=dictionary['portfolio']['cherry_pick']['symbols'],
            index_top_n=dictionary['portfolio']['index']['top_n'],
            index_exclude_symbols=dictionary['portfolio']['index']['exclude_symbols']
        )
        return self


@dataclass
class TelegramBotConfig:
    # no config needed yet
    @classmethod
    def from_config_yaml(cls, file_path):
        self = cls()
        return self


@dataclass
class SecretsStore:
    binance_test: ExchangeToken
    kraken_test: ExchangeToken
    binance: ExchangeToken
    kraken: ExchangeToken
    telegram: TelegramToken

    @classmethod
    def from_secrets_yaml(cls, file_path):
        file = Path(file_path)
        with open(file) as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                print("Error while parsing secrets file:")
                print(exc)
                raise exc
        self = cls.from_dict(data)
        return self

    @classmethod
    def from_dict(cls, dictionary):
        self = cls(
            binance_test=ExchangeToken(
                api_key=dictionary['exchanges']['testnet']['binance']['api_key'],
                secret=dictionary['exchanges']['testnet']['binance']['secret']
            ),
            kraken_test=ExchangeToken(
                api_key=dictionary['exchanges']['testnet']['kraken']['api_key'],
                secret=dictionary['exchanges']['testnet']['kraken']['secret']
            ),
            binance=ExchangeToken(
                api_key=dictionary['exchanges']['mainnet']['binance']['api_key'],
                secret=dictionary['exchanges']['mainnet']['binance']['secret']
            ),
            kraken=ExchangeToken(
                api_key=dictionary['exchanges']['mainnet']['kraken']['api_key'],
                secret=dictionary['exchanges']['mainnet']['kraken']['secret']
            ),
            telegram=TelegramToken(
                token=dictionary['telegram']['token'],
                chat_id=dictionary['telegram']['chat_id']
            )
        )
        return self


@dataclass
class Config:
    trading_bot_config: TradingBotConfig
    telegram_bot_config: TelegramBotConfig
    secrets: SecretsStore

    @classmethod
    def from_yaml_files(cls, config_yaml='config.yaml', secrets_yaml='secrets.yaml'):
        self = cls(
            trading_bot_config=TradingBotConfig.from_config_yaml(file_path=config_yaml),
            telegram_bot_config=TelegramBotConfig.from_config_yaml(file_path=config_yaml),
            secrets=SecretsStore.from_secrets_yaml(file_path=secrets_yaml)
        )
        return self
