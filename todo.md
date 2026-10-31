# Subscription Management System – TODO

This is our working checklist for the hackathon. We'll update it as we build, test things and make decisions. It's okay if the order changes a little as we go.

## Who is handling what?

- **Nijoy – Backend:** Django project structure, Django REST Framework, APIs, authentication, permissions and the main application logic. He'll also coordinate the overall backend structure.
- **Nivin – Frontend:** React setup, page layouts, UI, navigation, API integration and frontend testing.
- **Manav – Database:** PostgreSQL setup, data models, relationships, constraints, indexes and schema changes.
- **Albin – Testing:** Input validation, Django and React testing, checking edge cases, reporting bugs and retesting fixes.

We'll still need to work together. For example, the frontend depends on the API, the API depends on the database, and testing needs input from everyone.

We'll still need to work together. For example, the frontend depends on the API, the API depends on the database, and testing needs input from everyone.

## 1. Get the basics ready

- [ ] Read through the problem statement together and agree on what we're going to build first.
- [ ] Confirm the main user roles: Admin, Staff and Customer.
- [ ] Stick to the agreed stack: React, Django, Django REST Framework, PostgreSQL, Celery, Redis and Docker Compose.
- [ ] Set up a local PostgreSQL database. We'll use PostgreSQL as the project's database.
- [ ] Agree on the basic database structure and draw an ER diagram.
- [ ] Decide the REST API routes and agree on the request/response format before both sides build against them.
- [ ] Decide how JWT login, token refresh and logout will work.
- [ ] Create the GitHub repo and invite all four members.
- [ ] Create separate branches for our work. Don't push unfinished work straight to `main`.
- [ ] Add a `.env.example` and make sure passwords, secret keys and other credentials aren't committed.
- [ ] Set up Docker and Docker Compose so the team can start the frontend, backend, PostgreSQL and Redis consistently.
- [ ] Add basic setup instructions to the README so everyone can run the project.

## 2. Set up the project

### Nijoy – Django and backend

- [ ] Create the Django project and get it running locally.
- [ ] Split the backend into apps/modules based on features instead of putting everything in one place.
- [ ] Set up environment variables and database configuration.
- [ ] Set up Django REST Framework for the REST API.
- [ ] Keep models, serializers, views, permissions and business logic organised.
- [ ] Set up JWT authentication, including token access and refresh.
- [ ] Add role-based permissions for Admin, Staff and Customer.
- [ ] Set up Celery and connect it to Redis for background jobs.
- [ ] Add scheduled Celery tasks for subscription renewals and invoice generation.
- [ ] Make sure API errors are handled consistently.
- [ ] Add application logging and a simple health-check endpoint.

### Nivin – Frontend and web development

- [ ] Set up the React project and folder structure.
- [ ] Decide on the overall look: colours, fonts, spacing and common UI styles.
- [ ] Build the main layout and navigation.
- [ ] Create reusable buttons, form fields, tables, modals and status labels.
- [ ] Set up the REST API connection to Django.
- [ ] Add JWT-aware login and protected routes. Don't store sensitive tokens in an unsafe place.
- [ ] Add pages for the admin, staff and customer views.
- [ ] Add React tests for important components, forms and user flows.
- [ ] Include loading, empty, success and error states instead of leaving pages blank.
- [ ] Make the main screens work on both laptop and mobile sizes.

### Manav – Database and schemas

- [ ] Set up PostgreSQL and share the setup steps with everyone.
- [ ] Draw the ER diagram and go through it with Nijoy before the models are finalised.
- [ ] Plan the tables/models for:
  - [ ] Users and roles
  - [ ] Customers and staff
  - [ ] Products and product variants
  - [ ] Plans
  - [ ] Taxes
  - [ ] Quotations and quotation templates
  - [ ] Subscriptions and subscription lines
  - [ ] Discounts
  - [ ] Invoices and invoice lines
  - [ ] Payments
- [ ] Decide the fields, data types, primary keys and foreign keys for each model.
- [ ] Add the required unique constraints and relationships.
- [ ] Think through how prices, taxes, quantities, dates and billing intervals should be stored.
- [ ] Add indexes where they will help common searches and filters.
- [ ] Check constraints that prevent duplicate invoices for the same subscription and billing period.
- [ ] Coordinate schema changes with Nijoy and commit migrations to Git.

### Albin – Validation and testing

- [ ] Make a list of the features that need testing.
- [ ] Prepare Django tests for APIs, permissions, models and billing logic.
- [ ] Prepare React tests for key components, forms and important user flows.
- [ ] Write down what Admin, Staff and Customer should and shouldn't be able to do.
- [ ] Prepare test cases for valid, invalid, empty, duplicate and boundary inputs.
- [ ] Check each feature as it becomes available instead of leaving all testing until the end.
- [ ] Keep a simple bug list with steps to reproduce each issue.

## 3. Features to build

### Accounts and user roles

- [ ] Allow customers to register with an email and password.
- [ ] Make sure each email can be used for only one account.
- [ ] Password must be longer than 8 characters and include uppercase, lowercase and a special character.
- [ ] Add login and logout.
- [ ] Add password reset using a link sent to the registered email.
- [ ] Admin should have access to the full system.
- [ ] Staff should only have access to the features allowed for their role.
- [ ] Customers should only see their own subscriptions and invoices.
- [ ] Only Admin should be able to add staff members.

### Products and plans

- [ ] Admin can add, edit and view products.
- [ ] Each product should have a name, type, sales price, cost price and notes.
- [ ] Add support for product variants, such as different brands.
- [ ] Allow a variant to change the product price (the brief gives the Odoo brand example with an extra 560).
- [ ] Admin can create and manage plans.
- [ ] Plans should support daily, weekly, monthly and yearly billing.
- [ ] Add minimum quantity and plan availability dates.
- [ ] Add options for automatic closure, early closure, pause and renewal.
- [ ] Check that prices, quantities and dates are valid before saving.

### Quotations and subscriptions

- [ ] Create quotation templates with plans and product lines already added.
- [ ] Add a validity period to each quotation template.
- [ ] Allow staff to create a customer quotation from a template.
- [ ] Give each subscription a unique number.
- [ ] Store the customer, plan, start date, expiry date and payment terms.
- [ ] Subscription lines should include product, quantity, unit price, taxes and amount.
- [ ] Add the subscription statuses: Draft, Quotation, Confirmed, Active and Closed.
- [ ] Make it clear which stage each subscription is in.
- [ ] Prevent invalid status changes.

### Invoices and recurring billing

- [ ] Use Celery scheduled tasks to check which subscriptions are due for billing.
- [ ] Generate invoices from subscriptions when their billing date arrives.
- [ ] Fill in customer details, product lines, taxes and totals automatically.
- [ ] Calculate taxes using the rules set by Admin.
- [ ] Allow invoices to be confirmed, cancelled, sent and printed.
- [ ] Add the invoice statuses: Draft, Confirmed and Paid.
- [ ] Make sure running the billing task more than once doesn't create duplicate invoices.
- [ ] Make billing tasks safe to retry if a worker fails partway through.
- [ ] Make sure invoices aren't skipped when subscriptions become due.
- [ ] Show the next billing date and previous invoices for a subscription.

### Discounts

- [ ] Only Admin can create and manage discounts.
- [ ] Support fixed-amount and percentage discounts.
- [ ] Add minimum purchase amount or minimum quantity conditions.
- [ ] Add start date, end date and usage limit.
- [ ] Allow discounts to apply to selected products or a full subscription.
- [ ] Apply valid discounts automatically to the next invoice.
- [ ] Stop applying a discount after it expires or reaches its usage limit.

### Payments

- [ ] Allow staff to record a payment against an invoice.
- [ ] Store the payment method, amount, date and note.
- [ ] Update the invoice status when payment is recorded.
- [ ] Show which invoices are paid and which are still outstanding.
- [ ] Make overdue invoices easy to find.
- [ ] Decide whether to support partial payments once the main payment flow is working.

### Dashboard and reports

- [ ] Show the number of active subscriptions.
- [ ] Show revenue received and the amount still outstanding.
- [ ] Show overdue invoices.
- [ ] Add filters so staff can find the information they need.
- [ ] Make sure dashboard numbers come from the database, not hard-coded sample data.
- [ ] Check that the totals match the actual invoices and payments.

### Customer portal

- [ ] Let customers view their account details.
- [ ] Let customers see their subscriptions and current status.
- [ ] Let customers view their invoices and payment status.
- [ ] Check that a customer cannot access another customer's information by changing an ID or URL.

## 4. Testing and fixing things

Albin will coordinate testing, but everyone should test the features they build.

- [ ] Run Django's test suite for backend logic and APIs.
- [ ] Run the React test suite for components and user flows.
- [ ] Test Celery tasks, scheduled billing and retry behaviour.
- [ ] Test the app using Docker Compose, not just from individual local setups.

- [ ] Try registering with an invalid email, an existing email and a weak password.
- [ ] Try submitting forms with missing or incorrect values.
- [ ] Check that negative prices and invalid quantities are rejected.
- [ ] Check that users cannot access pages or API actions outside their role.
- [ ] Check that customers cannot see another customer's records.
- [ ] Test subscription pauses, renewals, expiry and early closure.
- [ ] Test tax and discount calculations with sample values we can verify manually.
- [ ] Run recurring billing more than once and check for duplicate invoices.
- [ ] Test payments and make sure the correct invoice is updated.
- [ ] Check overdue invoice and dashboard figures.
- [ ] Retest bugs after they're fixed.
- [ ] Keep track of anything that is still incomplete so we're clear about it during the demo.

## 5. GitHub and working together

- [ ] Everyone should make commits from their own account.
- [ ] Use branches for individual features or fixes.
- [ ] Write commit messages that explain the change, such as `feat: add subscription API` or `fix: validate invoice amount`.
- [ ] Push changes regularly so work doesn't pile up locally.
- [ ] Review important changes before merging them into `main`.
- [ ] Pull the latest changes before starting work.
- [ ] Let the team know before making changes that affect shared models or API routes.
- [ ] Don't commit `.env` files, passwords, secret keys or local database files.

## 6. Deployment and final checks

- [ ] Make sure the app can be started using Docker Compose.
- [ ] Check that configuration comes from environment variables and no secrets are committed.
- [ ] Add Nginx configuration for serving the app and forwarding requests to the backend.
- [ ] Check application logs and health-check endpoints.
- [ ] Confirm the Celery worker and scheduler are running in the deployment setup.

## 7. Before the presentation

- [ ] Add realistic sample data so we can demonstrate the system properly.
- [ ] Test the complete flow: customer signup → product and plan setup → quotation → subscription → invoice → payment → dashboard.
- [ ] Check the project from a fresh clone using the README instructions.
- [ ] Check the main pages and APIs with a realistic amount of data.
- [ ] Look for slow database queries and pages. The brief expects pages to respond in under two seconds, even with thousands of subscriptions.
- [ ] Prepare a short explanation of the database design and why we chose that structure.
- [ ] Be ready to explain the backend structure, API flow, validation and billing logic.
- [ ] Each of us should be able to explain the part we've worked on.
- [ ] Do one full practice demo together.
- [ ] Be clear about what's finished and what's still a limitation.

## Suggested order

1. Agree on the scope, database structure and API plan.
2. Nijoy sets up Django and DRF while Nivin starts the React app and Manav works on the PostgreSQL schema.
3. Bring up the services with Docker Compose and connect the database, backend and frontend.
4. Get JWT login and role permissions working before building the rest of the screens.
5. Build products, plans, quotations and subscriptions.
6. Set up Celery and Redis, then build scheduled invoice generation and recurring billing.
7. Add discounts, payments, the dashboard and customer portal.
8. Test the full flow, fix the important bugs and prepare the demo.

## Quick update before wrapping up each day

- [ ] What did I get done today?
- [ ] What am I picking up next?
- [ ] Am I waiting on anyone or blocked by something?
- [ ] Have I pushed my changes?
- [ ] Is there anything the others need to know?
