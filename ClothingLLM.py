from pydantic import BaseModel, conint
import enum


class Occasion_LLM(str, enum.Enum):
    sport = "sports"
    formal = "formal"
    casual = "casual"


class Fit_LLM(str, enum.Enum):
    oversized = "oversized"
    slim = "slim"
    regular = "regular"


class Sleeve_LLM(str, enum.Enum):
    long_sleeve = "long sleeve"
    short_sleeve = "short sleeve"
    sleeveless = "sleeveless"


class TypePants_LLM(str, enum.Enum):
    jeans = "jeans"
    sweatpants = "sweatpants"
    dress_pants = "dress pants"


class Weather_LLM(str, enum.Enum):
    rain = "rain"
    windy = "windy"
    snow = "snow"
    not_specified = "not_specified"


class Climate_LLM(str, enum.Enum):
    warm = "warm"
    cold = "cold"
    moderate = "moderate"


class ShoesType_LLM(str, enum.Enum):
    sneakers = "sneakers"
    boots = "boots"
    dress_shoes = "dress shoes"
    loafers = "loafers"
    sandals = "sandals"

class BottomType_LLM(str, enum.Enum):
    shorts = "shorts"
    long_pants = "regular"

class Category_LLM(str, enum.Enum):
    UNDERWEAR = "underwear"
    SHIRT = "shirt"
    BOTTOMS = "bottoms"
    JACKET = "jacket"
    SUIT = "suit"
    SWEATER_CARDIGAN = "sweater/cardigan"
    SHOES = "shoes"
    SOCKS = "socks"
    SWIMWEAR = "swimwear"
    ACCESSORIES = "accessories"

class ClothingCategory(BaseModel):
    name: str
    category: Category_LLM
class Underwear_LLM(BaseModel):
    name: str
    brand: str
    color: str
    occasion: Occasion_LLM


class Shirt_LLM(BaseModel):
    name: str
    brand: str
    color: str
    sleeve: Sleeve_LLM
    fit: Fit_LLM
    layering: bool
    occasion: Occasion_LLM


class Bottoms_LLM(BaseModel):
    name: str
    brand: str
    fit: Fit_LLM
    color: str
    length: BottomType_LLM
    occasion: Occasion_LLM
    type: TypePants_LLM


class Jacket_LLM(BaseModel):
    name: str
    brand: str
    weather: Weather_LLM
    climate: Climate_LLM
    occasion: Occasion_LLM


class Suit_LLM(BaseModel):
    name: str
    brand: str
    color: str
    preference: conint(ge=1, le=5)  # Suit preference (e.g., style, fit)


class SweaterCardigan_LLM(BaseModel):
    name: str
    brand: str
    color: str
    fit: Fit_LLM
    climate: Climate_LLM
    weather: Weather_LLM
    occasion: Occasion_LLM



class Shoes_LLM(BaseModel):
    name: str
    brand: str
    color: str
    type: ShoesType_LLM
    occasion: Occasion_LLM
    weather_suitability: Weather_LLM


class Socks_LLM(BaseModel):
    name: str
    brand: str
    occasion: Occasion_LLM


class Swimwear_LLM(BaseModel):
    name: str
    brand: str
    color: str


class Accessories_LLM(BaseModel):
    name: str
    brand: str
    type: str
    occasion: Occasion_LLM