from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from datetime import timezone
import datetime

from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, unique=True, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    messages = relationship("Message1")
    def __repr__(self):
        return "<User(FirstName='{}', LastName='{}')>" \
            .format(self.first_name, self.last_name)


class Message1(Base):
    __tablename__ = 'message'
    update_id = Column(Integer, primary_key=True, unique=True)
    text = Column(String)
    #date = Column(DateTime=datetime.datetime.utcnow())
    sender_id = Column(Integer, ForeignKey('user.id')) #ondelete="CASCADE"

    def __repr__(self):
        return "<Message(text='{}', date='{}', sender_id='{}')>" \
            .format(self.first_name, self.last_name, self.sender_id)


# class Chat(Base):

#   PRIVATE, GROUP = 'private', 'group'

#    TYPE_CHOICES = (
#        (PRIVATE, ('Private')),
#        (GROUP, ('Group')),
#    )

#    id = Column(Integer, primary_key=True)
#    type = models.CharField(max_length=255, choices=TYPE_CHOICES)
#    title = models.CharField(max_length=255, null=True, blank=True)
#    username = models.CharField(max_length=255, null=True, blank=True)
#    first_name = models.CharField(max_length=255, null=True, blank=True)
#    last_name = models.CharField(max_length=255, null=True, blank=True)
