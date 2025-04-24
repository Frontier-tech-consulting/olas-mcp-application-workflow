-- Enable the uuid-ossp extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    privy_user_id TEXT UNIQUE NOT NULL,
    email TEXT,
    wallet_address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- maintaining the user session state. --
CREATE TABLE IF NOT EXISTS public.session_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    privy_user_id TEXT UNIQUE NOT NULL,
    state JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on privy_user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_privy_user_id ON public.users(privy_user_id);

-- Create index on wallet_address for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_wallet_address ON public.users(wallet_address);

-- Enable Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations for authenticated users
CREATE POLICY "Allow all operations for authenticated users" 
ON public.users 
FOR ALL 
TO authenticated 
USING (true);

-- Create policy to allow read access for anonymous users
CREATE POLICY "Allow read access for anonymous users" 
ON public.users 
FOR SELECT 
TO anon 
USING (true); 