from flask import Flask, request, jsonify, session
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from models import db, User, Data
from sqlalchemy import func, extract
from datetime import datetime
from sqlalchemy import distinct
import mysql.connector

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://data:Test1234567890@localhost:3306/data_analysis'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = 'your_secret_key'  # Required for session management

# Initialize Extensions
bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True)
db.init_app(app)

# Create DB Tables
with app.app_context():
    db.create_all()

@app.route("/")
def hello_world():
    return "Hello, World!"



@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400  # Bad Request

    user_exists = User.query.filter_by(email=email).first() is not None
    if user_exists:
        return jsonify({"error": "Email already exists"}), 409  # Conflict

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # Ensure it's a string
    new_user = User(email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    session["user_id"] = new_user.id  # Store user session

    return jsonify({
        "id": new_user.id,
        "email": new_user.email
    }), 201  # Created

@app.route("/login", methods=["POST"])
def login_user():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401  # Unauthorized

    session["user_id"] = user.id

    return jsonify({
        "id": user.id,
        "email": user.email
    }), 200  # OK

@app.route("/api/sample-type-count", methods=["GET"])
def get_sample_type_count():
    """Fetch count of each Samp_Type within a date range."""
    try:
        # Get date filters from query parameters
        start_date = request.args.get("start_date")  # Format: YYYY-MM-DD
        end_date = request.args.get("end_date")      # Format: YYYY-MM-DD

        # Validate and parse dates
        filters = []
        if start_date:
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                filters.append(Data.testdate >= start_date)
            except ValueError:
                return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400

        if end_date:
            try:
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                filters.append(Data.testdate <= end_date)
            except ValueError:
                return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD"}), 400

        # Query the database with optional filters
        query = db.session.query(
            Data.Samp_Type, func.count(Data.Samp_Type).label("count_value")
        ).group_by(Data.Samp_Type)

        if filters:
            query = query.filter(*filters)

        results = query.all()

        # Convert results to dictionary format
        sample_type_counts = {row[0]: row[1] for row in results}

        return jsonify(sample_type_counts), 200  # Return JSON response

    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        return jsonify({"error": str(e)}), 500  # Internal Server Error



@app.route("/api/ship-hcu-count", methods=["GET"])
def get_ship_hcu_count():
    """Fetch count of 'HCU' in Samp_Type for each unique ship within a date range."""
    try:
        start_date = request.args.get("start_date")  # Format: YYYY-MM-DD
        end_date = request.args.get("end_date")  # Format: YYYY-MM-DD

        # Validate and parse dates
        filters = [Data.Samp_Type == "HCU"]
        if start_date:
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                filters.append(Data.testdate >= start_date)
            except ValueError:
                return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400

        if end_date:
            try:
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                filters.append(Data.testdate <= end_date)
            except ValueError:
                return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD"}), 400

        # Query with filters
        results = db.session.query(
            Data.Ship, func.count(Data.Samp_Type).label("hcu_count")
        ).filter(*filters).group_by(Data.Ship).all()

        ship_hcu_counts = {row[0]: row[1] for row in results}

        return jsonify(ship_hcu_counts), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/purifier-count", methods=["GET"])
def get_purifier_count():
    """Fetch count of 'Purifier' in Samp_Type for each unique ship within a date range."""
    try:
        # Get date filters from query parameters
        start_date = request.args.get("start_date")  # Format: YYYY-MM-DD
        end_date = request.args.get("end_date")      # Format: YYYY-MM-DD

        # Validate and parse dates
        filters = [Data.Samp_Type == "Purifier"]
        if start_date:
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                filters.append(Data.testdate >= start_date)
            except ValueError:
                return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400

        if end_date:
            try:
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                filters.append(Data.testdate <= end_date)
            except ValueError:
                return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD"}), 400

        # Query the database with optional filters
        query = db.session.query(
            Data.Ship, func.count(Data.Samp_Type).label("purifier_count")
        ).filter(*filters).group_by(Data.Ship)

        results = query.all()

        # Convert results to dictionary format
        purifier_counts = {row[0]: row[1] for row in results}

        return jsonify(purifier_counts), 200  # Return JSON response

    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        return jsonify({"error": str(e)}), 500  # Internal Server Error








@app.route('/api/ships', methods=['GET'])
def get_ships():
    try:
        ships = db.session.query(distinct(Data.Ship)).all()
        ship_names = [ship[0] for ship in ships if ship[0]]
        return jsonify(ship_names), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# @app.route('/api/ship-hcu-details', methods=['GET'])
# def get_ship_hcu_details():
#     try:
#         ship_name = request.args.get('ship')
#         start_year = request.args.get('startYear')
#         end_year = request.args.get('endYear')

#         if not ship_name or not start_year or not end_year:
#             return jsonify({'error': 'Missing required parameters'}), 400

#         start_date = datetime(int(start_year), 1, 1)
#         end_date = datetime(int(end_year), 12, 31)

#         results = db.session.query(
#             Data.Ship,
#             Data.testdate,
#             Data.vlims_lo_samp_point_Desc,
#             Data.VLIMS_PARTICLE_COUNT_4_MICRON_SCALE,
#             Data.VLIMS_PARTICLE_COUNT_6_MICRON_SCALE,
#             Data.VLIMS_PARTICLE_COUNT_14_MICRON_SCALE
#         ).filter(
#             Data.Ship == ship_name,
#             Data.testdate >= start_date,
#             Data.testdate <= end_date,
#             Data.vlims_lo_samp_point_Desc.like('HCU%')
#         ).order_by(Data.testdate).all()

#         if not results:
#             return jsonify({'message': 'No data found for the specified ship and year range'}), 404

#         data_list = [
#             {
#                 'Ship': row.Ship,
#                 'Sample_Point': row.vlims_lo_samp_point_Desc,
#                 'Test_Date': row.testdate.strftime('%Y-%m-%d'),
#                 'Particle_Count_4_Micron': row.VLIMS_PARTICLE_COUNT_4_MICRON_SCALE or 0.0,
#                 'Particle_Count_6_Micron': row.VLIMS_PARTICLE_COUNT_6_MICRON_SCALE or 0.0,
#                 'Particle_Count_14_Micron': row.VLIMS_PARTICLE_COUNT_14_MICRON_SCALE or 0.0
#             }
#             for row in results
#         ]

#         return jsonify(data_list), 200

#     except Exception as e:
#         db.session.rollback()
#         return jsonify({'error': str(e)}), 500
@app.route('/api/ship-hcu-details', methods=['GET'])
def get_ship_hcu_details():
    try:
        ship_name = request.args.get('ship')
        start_year = request.args.get('startYear')
        end_year = request.args.get('endYear')

        if not ship_name or not start_year or not end_year:
            return jsonify({'error': 'Missing required parameters'}), 400

        # Convert years to integers
        try:
            start_year = int(start_year)
            end_year = int(end_year)
        except ValueError:
            return jsonify({'error': 'Invalid year format. Use integers for years.'}), 400

        # Query using extract to filter by year
        results = db.session.query(
            Data.Ship,
            Data.testdate,
            Data.vlims_lo_samp_point_Desc,
            Data.VLIMS_PARTICLE_COUNT_4_MICRON_SCALE,
            Data.VLIMS_PARTICLE_COUNT_6_MICRON_SCALE,
            Data.VLIMS_PARTICLE_COUNT_14_MICRON_SCALE
        ).filter(
            Data.Ship == ship_name,
            extract('year', Data.testdate) >= start_year,
            extract('year', Data.testdate) <= end_year,
            Data.vlims_lo_samp_point_Desc.like('HCU%')
        ).order_by(Data.testdate).all()

        if not results:
            return jsonify({'message': 'No data found for the specified ship and year range'}), 404

        data_list = [
            {
                'Ship': row.Ship,
                'Sample_Point': row.vlims_lo_samp_point_Desc,
                'Test_Date': row.testdate.strftime('%Y-%m-%d'),
                'Particle_Count_4_Micron': row.VLIMS_PARTICLE_COUNT_4_MICRON_SCALE or 0.0,
                'Particle_Count_6_Micron': row.VLIMS_PARTICLE_COUNT_6_MICRON_SCALE or 0.0,
                'Particle_Count_14_Micron': row.VLIMS_PARTICLE_COUNT_14_MICRON_SCALE or 0.0
            }
            for row in results
        ]

        return jsonify(data_list), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# @app.route('/api/average-particle-count', methods=['GET'])
# def get_average_particle_count():
#     try:
#         ship_name = request.args.get('ship')
#         start_date = request.args.get('start_date')
#         end_date = request.args.get('end_date')

#         if not ship_name or not start_date or not end_date:
#             return jsonify({'error': 'Missing required parameters'}), 400

#         # Convert dates
#         try:
#             start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
#             end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
#         except ValueError:
#             return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

#         # Query the database for the averages
#         results = db.session.query(
#             Data.vlims_lo_samp_point_Desc,
#             func.avg(Data.VLIMS_PARTICLE_COUNT_4_MICRON_SCALE).label('avg_4_micron'),
#             func.avg(Data.VLIMS_PARTICLE_COUNT_6_MICRON_SCALE).label('avg_6_micron'),
#             func.avg(Data.VLIMS_PARTICLE_COUNT_14_MICRON_SCALE).label('avg_14_micron')
#         ).filter(
#             Data.Ship == ship_name,
#             Data.testdate >= start_date,
#             Data.testdate <= end_date,
#             Data.vlims_lo_samp_point_Desc.in_([f'HCU#{i}' for i in range(1, 10)])
#         ).group_by(Data.vlims_lo_samp_point_Desc).all()

#         if not results:
#             return jsonify({'message': 'No data found for the specified ship and date range'}), 404

#         # Format data
#         data_list = [
#             {
#                 'Ship': ship_name,
#                 'Sample_Point': row.vlims_lo_samp_point_Desc,
#                 'Average_Particle_Count_4_Micron': round(row.avg_4_micron, 2) if row.avg_4_micron else 0.0,
#                 'Average_Particle_Count_6_Micron': round(row.avg_6_micron, 2) if row.avg_6_micron else 0.0,
#                 'Average_Particle_Count_14_Micron': round(row.avg_14_micron, 2) if row.avg_14_micron else 0.0
#             }
#             for row in results
#         ]

#         return jsonify(data_list), 200

#     except Exception as e:
#         db.session.rollback()
#         return jsonify({'error': str(e)}), 500
@app.route('/api/average-particle-count', methods=['GET'])
def get_average_particle_count():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        ship_name = request.args.get('ship_name', None)

        if not start_date or not end_date:
            return jsonify({'error': 'Missing required parameters'}), 400

        # Convert dates
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        # Base query
        query = db.session.query(
            Data.vlims_lo_samp_point_Desc,
            func.avg(Data.VLIMS_PARTICLE_COUNT_4_MICRON_SCALE).label('avg_4_micron'),
            func.avg(Data.VLIMS_PARTICLE_COUNT_6_MICRON_SCALE).label('avg_6_micron'),
            func.avg(Data.VLIMS_PARTICLE_COUNT_14_MICRON_SCALE).label('avg_14_micron')
        ).filter(
            Data.testdate >= start_date,
            Data.testdate <= end_date,
            Data.vlims_lo_samp_point_Desc.in_([f'HCU#{i}' for i in range(1, 10)])
        )

        # Apply ship filter if ship_name is provided
        if ship_name and ship_name.lower() != 'all':
            query = query.filter(Data.Ship == ship_name)
        
        query = query.group_by(Data.vlims_lo_samp_point_Desc)
        results = query.all()

        if not results:
            return jsonify({'message': 'No data found for the specified date range'}), 404

        # Format data
        data_list = [
            {
                'Sample_Point': row.vlims_lo_samp_point_Desc,
                'Average_Particle_Count_4_Micron': round(row.avg_4_micron, 2) if row.avg_4_micron else 0.0,
                'Average_Particle_Count_6_Micron': round(row.avg_6_micron, 2) if row.avg_6_micron else 0.0,
                'Average_Particle_Count_14_Micron': round(row.avg_14_micron, 2) if row.avg_14_micron else 0.0
            }
            for row in results
        ]

        return jsonify(data_list), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# @app.route('/api/average-particle-count', methods=['GET'])
# def get_average_particle_count():
#     try:
#         start_date = request.args.get('start_date')
#         end_date = request.args.get('end_date')

#         if not start_date or not end_date:
#             return jsonify({'error': 'Missing required parameters'}), 400

#         # Convert dates
#         try:
#             start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
#             end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
#         except ValueError:



#             return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

#         # Query the database for the averages without filtering by ship name
#         results = db.session.query(
#             Data.Ship,
#             Data.vlims_lo_samp_point_Desc,
#             func.avg(Data.VLIMS_PARTICLE_COUNT_4_MICRON_SCALE).label('avg_4_micron'),
#             func.avg(Data.VLIMS_PARTICLE_COUNT_6_MICRON_SCALE).label('avg_6_micron'),
#             func.avg(Data.VLIMS_PARTICLE_COUNT_14_MICRON_SCALE).label('avg_14_micron')
#         ).filter(
#             Data.testdate >= start_date,
#             Data.testdate <= end_date,
#             Data.vlims_lo_samp_point_Desc.in_([f'HCU#{i}' for i in range(1, 10)])
#         ).group_by(Data.Ship, Data.vlims_lo_samp_point_Desc).all()

#         if not results:
#             return jsonify({'message': 'No data found for the specified date range'}), 404

#         # Format data
#         data_list = [
#             {
#                 'Ship': row.Ship,
#                 'Sample_Point': row.vlims_lo_samp_point_Desc,
#                 'Average_Particle_Count_4_Micron': round(row.avg_4_micron, 2) if row.avg_4_micron else 0.0,
#                 'Average_Particle_Count_6_Micron': round(row.avg_6_micron, 2) if row.avg_6_micron else 0.0,
#                 'Average_Particle_Count_14_Micron': round(row.avg_14_micron, 2) if row.avg_14_micron else 0.0
#             }
#             for row in results
#         ]

#         return jsonify(data_list), 200

#     except Exception as e:
#         db.session.rollback()
#         return jsonify({'error': str(e)}), 500



@app.route('/api/filtered-average-particle-count', methods=['GET'])
def filtered_average_particle_count():
    # Your logic here
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            return jsonify({'error': 'Missing required parameters'}), 400

        # Convert dates
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        # Query for BEFORE FILTER data
        before_filter_results = db.session.query(
            Data.Ship,
            func.avg(Data.VLIMS_PARTICLE_COUNT_4_MICRON_SCALE).label('avg_4_micron'),
            func.avg(Data.VLIMS_PARTICLE_COUNT_6_MICRON_SCALE).label('avg_6_micron'),
            func.avg(Data.VLIMS_PARTICLE_COUNT_14_MICRON_SCALE).label('avg_14_micron')
        ).filter(
            Data.testdate >= start_date,
            Data.testdate <= end_date,
            Data.vlims_lo_samp_point_Desc == 'BEFORE FILTER'
        ).group_by(Data.Ship).all()

        # Query for AFTER FILTER data
        after_filter_results = db.session.query(
            Data.Ship,
            func.avg(Data.VLIMS_PARTICLE_COUNT_4_MICRON_SCALE).label('avg_4_micron'),
            func.avg(Data.VLIMS_PARTICLE_COUNT_6_MICRON_SCALE).label('avg_6_micron'),
            func.avg(Data.VLIMS_PARTICLE_COUNT_14_MICRON_SCALE).label('avg_14_micron')
        ).filter(
            Data.testdate >= start_date,
            Data.testdate <= end_date,
            Data.vlims_lo_samp_point_Desc == 'AFTER FILTER'
        ).group_by(Data.Ship).all()

        # Format the results
        data_list = []
        for row in before_filter_results:
            data_list.append({
                'Ship': row.Ship,
                'vlims_lo_samp_point_Desc': 'BEFORE FILTER',
                'Average_Particle_Count_4_Micron': round(row.avg_4_micron, 2) if row.avg_4_micron else 0.0,
                'Average_Particle_Count_6_Micron': round(row.avg_6_micron, 2) if row.avg_6_micron else 0.0,
                'Average_Particle_Count_14_Micron': round(row.avg_14_micron, 2) if row.avg_14_micron else 0.0
            })

        for row in after_filter_results:
            data_list.append({
                'Ship': row.Ship,
                'vlims_lo_samp_point_Desc': 'AFTER FILTER',
                'Average_Particle_Count_4_Micron': round(row.avg_4_micron, 2) if row.avg_4_micron else 0.0,
                'Average_Particle_Count_6_Micron': round(row.avg_6_micron, 2) if row.avg_6_micron else 0.0,
                'Average_Particle_Count_14_Micron': round(row.avg_14_micron, 2) if row.avg_14_micron else 0.0
            })

        return jsonify(data_list), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True)


