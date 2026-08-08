from database.database import create_database


def main():
    print("Creating database...")

    create_database()

    print("Database created successfully!")


if __name__ == "__main__":
    main()