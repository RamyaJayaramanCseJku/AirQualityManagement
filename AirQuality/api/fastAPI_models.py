from sqlite3 import Timestamp
from xmlrpc.client import DateTime
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Union


class Token(BaseModel):
    access_token: str
    token_type: str


class UserAuthenticate(BaseModel):
    username: str
    password: str


class UserInfoBase(BaseModel):
    username: str

    class Config:
        orm_mode = True


class UserCreate(UserInfoBase):
    password: str


# Smart_Room
class Room_Object(BaseModel):
    room_id: str
    room_size: int
    people_count: int
    measurement_unit: str

    class Config:
        orm_mode = True


class Update_RoomObject(BaseModel):
    room_size: Optional[int] = None
    measurement_unit: Optional[str] = None
    people_count: Optional[int] = None

    class Config:
        orm_mode = True

# Air Quality


class AirQuality_Properties_Object(BaseModel):
    room_id: str
    device_id: str
    ventilator: str
    co2: float
    co2measurementunit: str
    temperature: float
    temperaturemeasurementunit: str
    humidity: float
    humiditymeasurementunit: str
    time: Timestamp

    class Config:
        orm_mode = True


class AirQuality_Temperature_Object(BaseModel):
    room_id: str
    ventilator: str
    temperature: int
    temperaturemeasurementunit: str
    time: Timestamp

    class Config:
        orm_mode = True


class AirQuality_Humidity_Object(BaseModel):
    room_id: str
    ventilator: str
    humidity: int
    humiditymeasurementunit: str
    time: Timestamp

    class Config:
        orm_mode = True


class AirQuality_Co2_Object(BaseModel):
    room_id: str
    ventilator: str
    co2: int
    co2measurementunit: str
    time: Timestamp

    class Config:
        orm_mode = True
