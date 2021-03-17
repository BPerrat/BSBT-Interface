from website.extensions import db
import datetime


class Cluster(db.Model):
    __tablename__ = 'clusters'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    #cluster = db.Column(db.Integer, nullable=False)


class Region(db.Model):
    __tablename__ = 'regions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    shapefile_id = db.Column(db.String(255), nullable=False)
    cluster_id = db.Column(db.Integer, db.ForeignKey('clusters.id'), nullable=False)

    cluster = db.relationship('Cluster', backref=db.backref('regions', lazy=True))


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    occupation = db.Column(db.String(200), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return '<User %d %r>' % (self.id, self.name)


class Ranking(db.Model):
    __tablename__ = 'rankings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    poorest = db.Column(
        db.Integer, db.ForeignKey('regions.id'), nullable=False)
    richest = db.Column(
        db.Integer, db.ForeignKey('regions.id'), nullable=False)
    reranked = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('rankings', lazy=True))

    def __repr__(self):
        return '<Ranking {} {} Poorest {} Richest {}>'.format(
            self.date, self.user_id, self.poorest, self.richest)


class SkippedRanking(db.Model):
    __tablename__ = 'skipped_rankings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    r1 = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)
    r2 = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('skipped_rankings', lazy=True))


class UnknowRegion(db.Model):
    __tablename__ = 'user_unknown_regions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    region_id = db.Column(
        db.Integer, db.ForeignKey('regions.id'), nullable=False)

    user = db.relationship(
        'User', backref=db.backref('unknown_regions', lazy=True))
    region = db.relationship(
        'Region', backref=db.backref('unknown_by_users', lazy=True))


class KnownRegion(db.Model):
    __tablename__ = 'user_known_regions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)

    user = db.relationship(
        'User', backref=db.backref('known_regions', lazy=True))
    bcluster = db.relationship(
        'Region', backref=db.backref('known_by_users', lazy=True))
