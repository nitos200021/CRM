import pandas as pd
from app import app
from models import db, House, WorkType

with app.app_context():
    def import_addresses(file_path):
        df = pd.read_excel(file_path, usecols=["Адрес", "Эт-ть"])
        for index, row in df.iterrows():
            address = row["Адрес"]
            floors = str(row["Эт-ть"])
            if not House.query.filter_by(address=address).first():
                new_house = House(address=address, floors=floors)
                db.session.add(new_house)
        db.session.commit()

    def import_faults(file_path):
        df = pd.read_excel(file_path, usecols=["№", "Вид неисправности"])
        for index, row in df.iterrows():
            fault = row["Вид неисправности"]
            if not WorkType.query.filter_by(name=fault).first():
                new_fault = WorkType(name=fault, description="")
                db.session.add(new_fault)
        db.session.commit()

    import_addresses("Адреса домов.xlsx")
    import_faults("Перечень неисправностей.xlsx")