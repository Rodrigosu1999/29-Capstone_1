"""Seed database with sample data from CSV Files."""


from app import db


db.drop_all()
db.create_all()
