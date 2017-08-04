from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tables import Base, Genre, Band, User

engine = create_engine('sqlite:///favoritemusic.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Create dummy user
User1 = User( name="Gavin McNamara", email="gavmcnamara@gmail.com",
             picture='AAEAAQAAAAAAAArWAAAAJDkzOTczOTA0LTI2ODItNDI2Ni04MmE4LWM2MDYxMDIxZGNlOA.jpg')
session.add(User1)
session.commit()

# Create Genre Jazz
genre3 = Genre(user_id = 1, name = "Jazz")

session.add(genre3)
session.commit()


jazz1 = Band(user_id=1, name = "Miles Davis", description = "An American jazz trumpeter, bandleader, and composer. He is among the most influential and acclaimed figures in the history of jazz and 20th century music.", year = "1944-1991", genre = genre3)

session.add(jazz1)
session.commit()

jazz2 = Band(user_id = 1, name = "Louis Armstrong", description = "an American trumpeter, composer, singer and occasional actor who was one of the most influential figures in jazz.", year = "1919-1970", genre = genre3)

session.add(jazz2)
session.commit()



# Create genre Rap/hip hop
genre4 = Genre(user_id = 1, name = "Rap/Hip Hop")

session.add(genre4)
session.commit()


hiphop1 = Band(user_id = 1, name = "Wu-Tang Clan", description = "The Wu-Tang Clan is an American hip hop group from Staten Island, New York City", year = "1992-Present", genre = genre4)

session.add(hiphop1)
session.commit()

hiphop2 = Band(user_id= 1, name = "The Beastie Boys", description = "The Beastie Boys were an American hip hop group from New York City, formed in 1981.", year = "1981-2012", genre = genre4)

session.add(hiphop2)
session.commit()


print "added items!"

