"""
Form validation utilities for Prontivus
Brazilian-specific validation with masks for CPF, dates, phones
"""

import re
from typing import Optional, Dict, Any
from datetime import datetime, date
import phonenumbers
from phonenumbers import NumberParseException

class BrazilianValidator:
    """Brazilian-specific validation utilities"""
    
    @staticmethod
    def validate_cpf(cpf: str) -> Dict[str, Any]:
        """Validate Brazilian CPF"""
        # Remove non-numeric characters
        cpf_clean = re.sub(r'[^0-9]', '', cpf)
        
        # Check length
        if len(cpf_clean) != 11:
            return {
                "valid": False,
                "error": "CPF deve ter 11 dígitos",
                "formatted": cpf
            }
        
        # Check for invalid sequences
        if cpf_clean in ['00000000000', '11111111111', '22222222222', '33333333333',
                         '44444444444', '55555555555', '66666666666', '77777777777',
                         '88888888888', '99999999999']:
            return {
                "valid": False,
                "error": "CPF inválido",
                "formatted": cpf
            }
        
        # Validate CPF algorithm
        def calculate_digit(cpf_digits, weights):
            sum_result = sum(int(digit) * weight for digit, weight in zip(cpf_digits, weights))
            remainder = sum_result % 11
            return 0 if remainder < 2 else 11 - remainder
        
        # Calculate first digit
        first_digit = calculate_digit(cpf_clean[:9], range(10, 1, -1))
        
        # Calculate second digit
        second_digit = calculate_digit(cpf_clean[:10], range(11, 1, -1))
        
        # Check if calculated digits match
        if int(cpf_clean[9]) == first_digit and int(cpf_clean[10]) == second_digit:
            return {
                "valid": True,
                "error": None,
                "formatted": BrazilianValidator.format_cpf(cpf_clean),
                "clean": cpf_clean
            }
        else:
            return {
                "valid": False,
                "error": "CPF inválido",
                "formatted": cpf
            }
    
    @staticmethod
    def format_cpf(cpf: str) -> str:
        """Format CPF with mask"""
        cpf_clean = re.sub(r'[^0-9]', '', cpf)
        if len(cpf_clean) == 11:
            return f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
        return cpf
    
    @staticmethod
    def validate_cnpj(cnpj: str) -> Dict[str, Any]:
        """Validate Brazilian CNPJ"""
        # Remove non-numeric characters
        cnpj_clean = re.sub(r'[^0-9]', '', cnpj)
        
        # Check length
        if len(cnpj_clean) != 14:
            return {
                "valid": False,
                "error": "CNPJ deve ter 14 dígitos",
                "formatted": cnpj
            }
        
        # Check for invalid sequences
        if cnpj_clean in ['00000000000000', '11111111111111', '22222222222222', '33333333333333',
                         '44444444444444', '55555555555555', '66666666666666', '77777777777777',
                         '88888888888888', '99999999999999']:
            return {
                "valid": False,
                "error": "CNPJ inválido",
                "formatted": cnpj
            }
        
        # Validate CNPJ algorithm
        def calculate_cnpj_digit(cnpj_digits, weights):
            sum_result = sum(int(digit) * weight for digit, weight in zip(cnpj_digits, weights))
            remainder = sum_result % 11
            return 0 if remainder < 2 else 11 - remainder
        
        # Calculate first digit
        first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        first_digit = calculate_cnpj_digit(cnpj_clean[:12], first_weights)
        
        # Calculate second digit
        second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        second_digit = calculate_cnpj_digit(cnpj_clean[:13], second_weights)
        
        # Check if calculated digits match
        if int(cnpj_clean[12]) == first_digit and int(cnpj_clean[13]) == second_digit:
            return {
                "valid": True,
                "error": None,
                "formatted": BrazilianValidator.format_cnpj(cnpj_clean),
                "clean": cnpj_clean
            }
        else:
            return {
                "valid": False,
                "error": "CNPJ inválido",
                "formatted": cnpj
            }
    
    @staticmethod
    def format_cnpj(cnpj: str) -> str:
        """Format CNPJ with mask"""
        cnpj_clean = re.sub(r'[^0-9]', '', cnpj)
        if len(cnpj_clean) == 14:
            return f"{cnpj_clean[:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:]}"
        return cnpj
    
    @staticmethod
    def validate_phone(phone: str) -> Dict[str, Any]:
        """Validate Brazilian phone number"""
        # Remove non-numeric characters
        phone_clean = re.sub(r'[^0-9]', '', phone)
        
        # Add country code if not present
        if not phone_clean.startswith('55'):
            phone_clean = '55' + phone_clean
        
        try:
            # Parse phone number
            parsed_phone = phonenumbers.parse(phone_clean, 'BR')
            
            if phonenumbers.is_valid_number(parsed_phone):
                return {
                    "valid": True,
                    "error": None,
                    "formatted": BrazilianValidator.format_phone(phone_clean),
                    "clean": phone_clean,
                    "international": phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
                    "national": phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.NATIONAL)
                }
            else:
                return {
                    "valid": False,
                    "error": "Número de telefone inválido",
                    "formatted": phone
                }
        except NumberParseException:
            return {
                "valid": False,
                "error": "Formato de telefone inválido",
                "formatted": phone
            }
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """Format Brazilian phone number with mask"""
        phone_clean = re.sub(r'[^0-9]', '', phone)
        
        # Remove country code for formatting
        if phone_clean.startswith('55') and len(phone_clean) > 10:
            phone_clean = phone_clean[2:]
        
        if len(phone_clean) == 10:  # Landline
            return f"({phone_clean[:2]}) {phone_clean[2:6]}-{phone_clean[6:]}"
        elif len(phone_clean) == 11:  # Mobile
            return f"({phone_clean[:2]}) {phone_clean[2:7]}-{phone_clean[7:]}"
        else:
            return phone
    
    @staticmethod
    def validate_date(date_str: str, format_str: str = "%d/%m/%Y") -> Dict[str, Any]:
        """Validate date string"""
        try:
            parsed_date = datetime.strptime(date_str, format_str).date()
            
            # Check if date is not in the future (for birth dates)
            if parsed_date > date.today():
                return {
                    "valid": False,
                    "error": "Data não pode ser futura",
                    "formatted": date_str,
                    "parsed": parsed_date
                }
            
            return {
                "valid": True,
                "error": None,
                "formatted": date_str,
                "parsed": parsed_date
            }
        except ValueError:
            return {
                "valid": False,
                "error": f"Data inválida. Use o formato {format_str}",
                "formatted": date_str
            }
    
    @staticmethod
    def format_date(date_obj: date, format_str: str = "%d/%m/%Y") -> str:
        """Format date object to string"""
        return date_obj.strftime(format_str)
    
    @staticmethod
    def validate_email(email: str) -> Dict[str, Any]:
        """Validate email address"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if re.match(email_pattern, email):
            return {
                "valid": True,
                "error": None,
                "formatted": email.lower()
            }
        else:
            return {
                "valid": False,
                "error": "Email inválido",
                "formatted": email
            }
    
    @staticmethod
    def validate_crm(crm: str, state: str = "SP") -> Dict[str, Any]:
        """Validate Brazilian medical license (CRM)"""
        # Remove non-numeric characters
        crm_clean = re.sub(r'[^0-9]', '', crm)
        
        # Check length (usually 4-6 digits)
        if len(crm_clean) < 4 or len(crm_clean) > 6:
            return {
                "valid": False,
                "error": "CRM deve ter entre 4 e 6 dígitos",
                "formatted": crm
            }
        
        return {
            "valid": True,
            "error": None,
            "formatted": f"{crm_clean}-{state}",
            "clean": crm_clean
        }
    
    @staticmethod
    def format_crm(crm: str, state: str = "SP") -> str:
        """Format CRM with state"""
        crm_clean = re.sub(r'[^0-9]', '', crm)
        return f"{crm_clean}-{state}"

class FormValidator:
    """Form validation with Brazilian masks"""
    
    @staticmethod
    def validate_patient_form(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate patient registration form"""
        errors = {}
        validated_data = {}
        
        # Name validation
        if not data.get('full_name') or len(data['full_name'].strip()) < 2:
            errors['full_name'] = "Nome completo é obrigatório (mínimo 2 caracteres)"
        else:
            validated_data['full_name'] = data['full_name'].strip()
        
        # CPF validation
        if data.get('cpf'):
            cpf_result = BrazilianValidator.validate_cpf(data['cpf'])
            if not cpf_result['valid']:
                errors['cpf'] = cpf_result['error']
            else:
                validated_data['cpf'] = cpf_result['clean']
                validated_data['cpf_formatted'] = cpf_result['formatted']
        
        # Email validation
        if data.get('email'):
            email_result = BrazilianValidator.validate_email(data['email'])
            if not email_result['valid']:
                errors['email'] = email_result['error']
            else:
                validated_data['email'] = email_result['formatted']
        
        # Phone validation
        if data.get('phone'):
            phone_result = BrazilianValidator.validate_phone(data['phone'])
            if not phone_result['valid']:
                errors['phone'] = phone_result['error']
            else:
                validated_data['phone'] = phone_result['clean']
                validated_data['phone_formatted'] = phone_result['formatted']
        
        # Birth date validation
        if data.get('birth_date'):
            date_result = BrazilianValidator.validate_date(data['birth_date'])
            if not date_result['valid']:
                errors['birth_date'] = date_result['error']
            else:
                validated_data['birth_date'] = date_result['parsed']
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "data": validated_data
        }
    
    @staticmethod
    def validate_doctor_form(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate doctor registration form"""
        errors = {}
        validated_data = {}
        
        # Name validation
        if not data.get('full_name') or len(data['full_name'].strip()) < 2:
            errors['full_name'] = "Nome completo é obrigatório (mínimo 2 caracteres)"
        else:
            validated_data['full_name'] = data['full_name'].strip()
        
        # CRM validation
        if data.get('crm'):
            crm_result = BrazilianValidator.validate_crm(data['crm'], data.get('state', 'SP'))
            if not crm_result['valid']:
                errors['crm'] = crm_result['error']
            else:
                validated_data['crm'] = crm_result['formatted']
        
        # Email validation
        if data.get('email'):
            email_result = BrazilianValidator.validate_email(data['email'])
            if not email_result['valid']:
                errors['email'] = email_result['error']
            else:
                validated_data['email'] = email_result['formatted']
        
        # Phone validation
        if data.get('phone'):
            phone_result = BrazilianValidator.validate_phone(data['phone'])
            if not phone_result['valid']:
                errors['phone'] = phone_result['error']
            else:
                validated_data['phone'] = phone_result['clean']
                validated_data['phone_formatted'] = phone_result['formatted']
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "data": validated_data
        }
