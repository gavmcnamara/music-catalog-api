import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Genre(Base):
    __tablename__ = 'genre'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

class Band(Base):
    __tablename__ = 'band'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    year = Column(String(20))
    genre_id = Column(Integer, ForeignKey('genre.id'))
    genre = relationship(Genre)


####insert at end of file#########

engine = create_engine('sqlite:///genresofmusic.db')
Base.metadata.create_all(engine)
