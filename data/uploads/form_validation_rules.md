# FORM VALIDATION RULES — CHECKOUT MODULE

## 1. Overview
This document defines the client-side and expected backend-side validation rules for the checkout form. Validation must be consistent across UI, API, and automated test flows.

---

## 2. Field-Level Validation

### 2.1 Full Name
- Mandatory field.
- Must contain only alphabetic characters and spaces.
- Minimum length: 3 characters.
- Error message: "Name is required." OR "Name must contain only letters."

### 2.2 Email
- Mandatory field.
- Must follow standard email format:
  - Contains '@'
  - Contains at least one period '.' after '@'
- Error message: "Invalid email address."

### 2.3 Address
- Mandatory field.
- Cannot contain special characters such as *, <, >.
- Minimum length: 5 characters.
- Error message: "Address is required."

### 2.4 Phone Number (Optional)
- If provided:
  - Must be exactly 10 digits.
  - No letters or symbols allowed.
- Error message: "Phone number must be 10 digits."

### 2.5 Shipping Method
- Default selection: Standard (Free).
- Express adds $10.

### 2.6 Discount Code (Optional)
- Must match a valid promo code:
  - SAVE10
  - FREESHIP
  - WELCOME5 (if enabled)
- Error message for invalid input: "Invalid Code"

---

## 3. Validation Trigger Conditions

- Real-time validation for email using on-field blur event (if enabled).
- Full validation occurs:
  - On clicking “Apply Discount”
  - On clicking “Pay Now”
  - On form submission

---

## 4. UI Behavior After Validation

- Errors must appear in red below each field.
- Errors must be cleared once the input becomes valid.
- On success:
  - The message "Payment Successful!" appears in green.
