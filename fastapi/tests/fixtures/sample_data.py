"""
Sample data fixtures for testing
"""
import factory
import pandas as pd
from datetime import datetime, timedelta
from factory import Faker, SubFactory, LazyAttribute
from models.hub_token import TokenResponse, TokenStatus


class TokenResponseFactory(factory.Factory):
    """Factory for TokenResponse model"""
    
    class Meta:
        model = dict  # Using dict since we're testing API responses
    
    id = factory.Sequence(lambda n: n)
    user_login = factory.LazyAttribute(lambda obj: f"USER{obj.id}.A{12345 + obj.id}")
    token = factory.LazyFunction(lambda: f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_token_{factory.Faker('uuid4')}")
    expires_at = factory.LazyFunction(lambda: datetime.now() + timedelta(hours=1))
    extracted_at = factory.LazyFunction(datetime.now)
    created_at = factory.LazyFunction(datetime.now)


class TokenStatusFactory(factory.Factory):
    """Factory for TokenStatus model"""
    
    class Meta:
        model = dict
    
    user_login = factory.Sequence(lambda n: f"USER{n}.A{12345 + n}")
    has_valid_token = True
    expires_at = factory.LazyFunction(lambda: datetime.now() + timedelta(hours=1))
    extracted_at = factory.LazyFunction(datetime.now)
    time_until_expiry = "59 minutes"


class HubCredentialsFactory(factory.Factory):
    """Factory for Hub credentials"""
    
    class Meta:
        model = dict
    
    user_login = factory.Sequence(lambda n: f"SILVA{n}.A{12345 + n}")
    password = factory.Faker('password', length=12)
    mfa_code = factory.LazyFunction(lambda: f"{factory.Faker('random_int', min=100000, max=999999).generate()}")


class FixedIncomeDataFactory(factory.Factory):
    """Factory for fixed income data"""
    
    class Meta:
        model = dict
    
    ativo = factory.Faker('company')
    instrumento = factory.Faker('random_element', elements=('CDB', 'CRI', 'NTN-F', 'LCA', 'LCI'))
    duration = factory.Faker('pyfloat', positive=True, max_value=10, right_digits=2)
    indexador = factory.Faker('random_element', elements=('CDI', 'IPCA', 'SELIC'))
    juros = factory.Faker('random_element', elements=('Mensal', 'Semestral'))
    primeira_data_juros = factory.Faker('date_between', start_date='today', end_date='+1y')
    isento = factory.Faker('random_element', elements=('Sim', 'Não'))
    rating = factory.Faker('random_element', elements=('AAA', 'AA', 'A', 'BBB', 'BB'))
    vencimento = factory.Faker('date_between', start_date='+1y', end_date='+10y')
    tax_min = factory.LazyAttribute(lambda obj: f"{factory.Faker('pyfloat', positive=True, max_value=15, right_digits=2).generate():.2f}%")
    tax_min_clean = factory.Faker('pyfloat', positive=True, max_value=15, right_digits=2)
    roa_aprox = factory.Faker('pyfloat', positive=True, max_value=10, right_digits=2)
    taxa_emissao = factory.Faker('pyfloat', positive=True, max_value=5, right_digits=2)
    publico = factory.Faker('random_element', elements=('Geral', 'Qualificado', 'Profissional'))
    publico_resumido = factory.LazyAttribute(lambda obj: {
        'Geral': 'R',
        'Qualificado': 'Q', 
        'Profissional': 'P'
    }[obj.publico])
    emissor = factory.Faker('company')
    cupom = factory.LazyAttribute(lambda obj: 'Jun/Dez' if obj.juros == 'Semestral' else '')
    classificar_vencimento = factory.LazyAttribute(lambda obj: f"[{((obj.vencimento - datetime.now().date()).days // 365) + 1} Anos]")
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)


def create_sample_dataframe(num_rows=10):
    """Create sample pandas DataFrame for testing"""
    data = [FixedIncomeDataFactory() for _ in range(num_rows)]
    
    # Convert to DataFrame format expected by the application
    df_data = []
    for item in data:
        df_row = {
            'Ativo': item['ativo'],
            'Instrumento': item['instrumento'],
            'Duration': item['duration'],
            'Indexador': item['indexador'],
            'Juros': item['juros'],
            'Primeira Data Juros': item['primeira_data_juros'],
            'Isento': item['isento'],
            'Rating.1': item['rating'],
            'Vencimento': item['vencimento'],
            'Tax.Mín': item['tax_min'],
            'ROA aprox.': f"{item['roa_aprox']:.2f}%",
            'Taxa de Emissão': f"{item['taxa_emissao']:.2f}%",
            'Público': item['publico']
        }
        df_data.append(df_row)
    
    return pd.DataFrame(df_data)


def create_sample_excel_data():
    """Create sample Excel-like data for download testing"""
    return {
        'CP': create_sample_dataframe(50),
        'EB': create_sample_dataframe(30),
        'TPF': create_sample_dataframe(20)
    }


class DatabaseRowFactory(factory.Factory):
    """Factory for database rows"""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n)
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)


class TokenDatabaseRowFactory(DatabaseRowFactory):
    """Factory for token database rows"""
    
    user_login = factory.Sequence(lambda n: f"USER{n}.A{12345 + n}")
    token = factory.LazyFunction(lambda: f"hub_token_{factory.Faker('uuid4')}")
    expires_at = factory.LazyFunction(lambda: datetime.now() + timedelta(hours=1))
    extracted_at = factory.LazyFunction(datetime.now)


class FixedIncomeDatabaseRowFactory(DatabaseRowFactory):
    """Factory for fixed income database rows"""
    
    data_coleta = factory.LazyFunction(datetime.now)
    ativo = factory.Faker('company')
    instrumento = factory.Faker('random_element', elements=('CDB', 'CRI', 'NTN-F'))
    duration = factory.Faker('pyfloat', positive=True, max_value=10, right_digits=6)
    indexador = factory.Faker('random_element', elements=('CDI', 'IPCA', 'SELIC'))
    juros = factory.Faker('random_element', elements=('Mensal', 'Semestral'))
    primeira_data_juros = factory.Faker('date_between', start_date='today', end_date='+1y')
    isento = factory.Faker('random_element', elements=('Sim', 'Não'))
    rating = factory.Faker('random_element', elements=('AAA', 'AA', 'A'))
    vencimento = factory.Faker('date_between', start_date='+1y', end_date='+10y')
    tax_min = factory.LazyAttribute(lambda obj: f"{factory.Faker('pyfloat', positive=True, max_value=15, right_digits=2).generate():.2f}%")
    tax_min_clean = factory.Faker('pyfloat', positive=True, max_value=15, right_digits=4)
    roa_aprox = factory.Faker('pyfloat', positive=True, max_value=10, right_digits=4)
    taxa_emissao = factory.Faker('pyfloat', positive=True, max_value=5, right_digits=4)
    publico = factory.Faker('random_element', elements=('Geral', 'Qualificado', 'Profissional'))
    publico_resumido = factory.LazyAttribute(lambda obj: {
        'Geral': 'R',
        'Qualificado': 'Q',
        'Profissional': 'P'
    }[obj.publico])
    emissor = factory.Faker('company')
    cupom = factory.LazyAttribute(lambda obj: 'Jun/Dez' if obj.juros == 'Semestral' else '')


# Pre-built sample data sets
SAMPLE_CREDENTIALS = {
    "valid": {
        "user_login": "SILVA.A12345",
        "password": "validpassword123",
        "mfa_code": "123456"
    },
    "invalid_username": {
        "user_login": "invalid_format",
        "password": "validpassword123", 
        "mfa_code": "123456"
    },
    "short_password": {
        "user_login": "SILVA.A12345",
        "password": "123",
        "mfa_code": "123456"
    },
    "invalid_mfa": {
        "user_login": "SILVA.A12345",
        "password": "validpassword123",
        "mfa_code": "12345"
    }
}

SAMPLE_TOKENS = [
    {
        "id": 1,
        "user_login": "SILVA.A12345",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.sample_token_1",
        "expires_at": datetime.now() + timedelta(hours=1),
        "extracted_at": datetime.now(),
        "created_at": datetime.now(),
        "is_expired": False
    },
    {
        "id": 2,
        "user_login": "SANTOS.B67890",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.sample_token_2",
        "expires_at": datetime.now() - timedelta(hours=1),
        "extracted_at": datetime.now() - timedelta(hours=2),
        "created_at": datetime.now() - timedelta(hours=2),
        "is_expired": True
    }
]

SAMPLE_FIXED_INCOME_STATS = {
    "total_records": 150,
    "unique_issuers": 25,
    "unique_indexers": 5,
    "last_update": datetime.now().isoformat(),
    "earliest_maturity": (datetime.now() + timedelta(days=30)).date().isoformat(),
    "latest_maturity": (datetime.now() + timedelta(days=3650)).date().isoformat()
}

# Utility functions for test data
def get_sample_credentials(scenario="valid"):
    """Get sample credentials for different test scenarios"""
    return SAMPLE_CREDENTIALS.get(scenario, SAMPLE_CREDENTIALS["valid"]).copy()

def get_sample_token(expired=False):
    """Get sample token data"""
    return SAMPLE_TOKENS[1 if expired else 0].copy()

def get_multiple_tokens(count=5):
    """Generate multiple token records"""
    return [TokenDatabaseRowFactory() for _ in range(count)]