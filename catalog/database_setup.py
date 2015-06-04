from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy_imageattach.entity import Image, \
    image_attachment, store_context
from sqlalchemy_imageattach.stores.fs import FileSystemStore

UPLOADED_PHOTOS_DEST = '/vagrant/catalog_new/app/static/images'
local_storage = FileSystemStore(path=UPLOADED_PHOTOS_DEST,
                                base_url='/static/images')

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
        }


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    added = Column(DateTime, default=func.now())

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class CategoryItem(Base):
    __tablename__ = 'category_item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    picture = image_attachment('ItemPicture')
    added = Column(DateTime, default=func.now())

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        with store_context(local_storage):
            return {
                'name': self.name,
                'description': self.description,
                'id': self.id,
                'picture': self.picture.locate(),
                'thumbnail': self.picture.find_thumbnail(width=300).locate()
            }


class ItemPicture(Base, Image):
    __tablename__ = 'item_picture'

    item_id = Column(Integer, ForeignKey('category_item.id'), primary_key=True)
    item = relationship(CategoryItem)

engine = create_engine('postgresql://vagrant:vagrant@localhost/test')

Base.metadata.create_all(engine)
