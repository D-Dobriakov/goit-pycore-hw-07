import functools
from datetime import datetime, timedelta
from collections import UserDict


class Field:
    '''
    Базовий клас для полів запису
    '''
    def __init__(self, value: Any) -> None:
        self.value = value
    
    def __str__(self) -> str:
        return str(self.value)
    

class Name(Field):
    '''
    Клас для імені контакту
    '''
    pass


class Phone(Field):
    '''
    Клас для номера телефону контакту з валідацією
    '''
    def __init__(self, value: str) -> None:
        if not (len(value) == 10 and value.isdigit()):
            raise ValueError("Phone number must be 10 digits long and contain only numbers.")
        super().__init__(value)


class Birthday(Field):
    '''
    Клас для дати народження з валідацією формату
    '''
    def __init__(self, value: str) -> None:
        try:
            self.value = datetime.strptime(value, "%d-%m-%Y").date()
        except ValueError:
            raise ValueError("Birthday must be in the format DD-MM-YYYY.")
        
    def __str__(self) -> str:
        return self.value.strftime("%d-%m-%Y")


class Record:
    '''
    Клас для запису контакту, який містить ім'я, список телефонів та дату народження
    '''
    def __init__(self, name: str) -> None:
        self.name = Name(name)
        self.phones = []
        self.birthday = None
    
    def add_phone(self, phone: str) -> None:
        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str) -> None:
        self.phones = [p for p in self.phones if p.value != phone]  
    
    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        for i, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[i] = Phone(new_phone)
                return
        raise ValueError("Phone number not found.")
    
    def find_phone(self, phone: str) -> Phone:
        for p in self.phones:
            if p.value == phone:
                return p
        return None
    
    def add_birthday(self, birthday: str) -> None:
        self.birthday = Birthday(birthday)

    def __str__(self) -> str:
        birthday_str = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}{birthday_str}"
    

class AddressBook(UserDict):
    '''
    Клас для адресної книги, який містить записи контактів
    '''
    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record
    
    def remove_record(self, name: str) -> None:
        if name in self.data:
            del self.data[name]
    
    def find_record(self, name: str) -> Record:
        return self.data.get(name, None)
    
    def get_upcoming_birthdays(self) -> list[dict[str, str]]:
        '''
        Метод для отримання списку контактів з днями народження, що наближаються
        '''
        upcoming_birthdays = []
        today = datetime.now().date()

        for record in self.data.values():
            if not record.birthday:
                continue
    
            birthday_this_year = record.birthday.value.replace(year=today.year)

            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            delta_days = (birthday_this_year - today).days

            if 0 <= delta_days <= 7:
                congratulation_date = birthday_this_year

                if congratulation_date.weekday() == 5:  # Saturday
                    congratulation_date += timedelta(days=2)
                elif congratulation_date.weekday() == 6:  # Sunday
                    congratulation_date += timedelta(days=1)
                
                upcoming_birthdays.append({
                    "name": record.name.value,
                    "congratulation_date": congratulation_date.strftime("%d-%m-%Y")
                })
        return upcoming_birthdays
    

def input_error_handler(func):
    '''
    Декоратор для обробки помилок введення даних
    '''
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Not enough arguments provided."
    return wrapper

def parse_input(user_input: str) -> tuple[str, list[str]]:
    '''
    Функція для парсингу введеного користувачем рядка в команду та аргументи
    '''
    if not user_input.strip():
        return "", []
    command, *args = user_input.split()
    command = command.strip().lower()
    return command, args

@input_error_handler
def add_contact(args: list[str], address_book: AddressBook) -> str:
    name, phone, *_ = args
    record = address_book.find_record(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        address_book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error_handler
def change_contact(args: list[str], address_book: AddressBook) -> str:
    name, old_phone, new_phone = args
    record = address_book.find_record(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return "Contact updated."
    return "Contact not found."

@input_error_handler
def show_contact(args: list[str], address_book: AddressBook) -> str:
    name = args[0]
    record = address_book.find_record(name)
    if record:
        return f"{name}: {', '.join(p.value for p in record.phones)}"
    return "Contact not found."

@input_error_handler
def show_all_contacts(address_book: AddressBook) -> str:
    if not address_book.data:
        return "No contacts found."
    return "\n".join(str(record) for record in address_book.data.values())

@input_error_handler
def add_birthday(args: list[str], address_book: AddressBook) -> str:
    name, birthday = args
    record = address_book.find_record(name)
    if record:
        record.add_birthday(birthday)
        return "Birthday added."
    return "Contact not found."

@input_error_handler
def show_birthday(args: list[str], address_book: AddressBook) -> str:
    name = args[0]
    record = address_book.find_record(name)
    if record and record.birthday:
        return f"{name}'s birthday: {record.birthday}"
    elif record:
        return f"{name} does not have a birthday set."
    return "Contact not found or birthday not set."

@input_error_handler
def birthdays(book: AddressBook) -> str:
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays."
    return "\n".join(f"{item['name']} - congratulation date: {item['congratulation_date']}" for item in upcoming)

def main() -> None:
    address_book: AddressBook = AddressBook()
    print("Welcome to the assistant bot!")

    while True:
        user_input: str = input("Enter command: ")
        command, args = parse_input(user_input)

        if not command:
            continue

        if command in ["exit", "close", "good bye"]:
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, address_book))

        elif command == "change":
            print(change_contact(args, address_book))

        elif command == "phone":
            print(show_contact(args, address_book))

        elif command == "add-birthday":
            print(add_birthday(args, address_book))

        elif command == "show-birthday":
            print(show_birthday(args, address_book))

        elif command == "birthdays":
            print(birthdays(address_book))

        else:
            print("Unknown command. Please try again.")


if __name__ == "__main__":    
    main()