# Supabase Setup Instructions

This document provides instructions on how to set up the Supabase database for the OLAS DeFi Strategy Finder application.

## Option 1: Using the Python Initialization Script

1. Make sure your `.env` file contains the correct Supabase credentials:
   ```
   SUPABASE_URL=postgresql://postgres.[PROJECT_ID]:[PASSWORD]@[HOST]:[PORT]/postgres
   SUPABASE_KEY=your_supabase_key
   ```

2. Run the initialization script:
   ```bash
   python init_supabase.py
   ```

   This script will:
   - Connect to your Supabase instance
   - Check if the `users` table already exists
   - If the table doesn't exist, it will provide instructions for manual setup

## Option 2: Using the SQL Script in Supabase Dashboard (Recommended)

1. Log in to your Supabase dashboard at https://app.supabase.com
2. Select your project
3. Go to the SQL Editor
4. Copy the contents of `init_supabase.sql`
5. Paste the SQL into the editor and run it

## Table Schema

The `users` table has the following schema:

| Column         | Type                     | Description                                |
|----------------|--------------------------|--------------------------------------------|
| id             | UUID                     | Primary key, auto-generated                |
| privy_user_id  | TEXT                     | Unique identifier from Privy authentication |
| email          | TEXT                     | User's email address                       |
| wallet_address | TEXT                     | User's wallet address                      |
| created_at     | TIMESTAMP WITH TIME ZONE | When the user was created                  |
| updated_at     | TIMESTAMP WITH TIME ZONE | When the user was last updated             |

## Troubleshooting

If you encounter any issues:

1. Check that your Supabase URL and key are correct in the `.env` file
2. Verify that your Supabase project has the necessary permissions
3. Check the logs for any specific error messages
4. Make sure the `uuid-ossp` extension is enabled in your Supabase project (for UUID generation)
5. If you see an error about the `exec_sql` function, use Option 2 (SQL Script) instead

## Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction) 