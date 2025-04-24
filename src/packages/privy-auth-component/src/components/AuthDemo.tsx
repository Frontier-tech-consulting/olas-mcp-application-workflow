import React from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

const AuthDemo = () => {
  return (
    <div className="container mx-auto py-10">
      <h1 className="text-3xl font-bold mb-8 text-olas">OLAS MCP Privy Authentication</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <Card>
          <CardHeader>
            <CardTitle>Privy Authentication</CardTitle>
            <CardDescription>
              Connect users with email, social accounts, or wallet
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p>
                The Privy authentication component allows users to log in using:
              </p>
              <ul className="list-disc pl-5 space-y-2">
                <li>Email address</li>
                <li>Social accounts (Google, Twitter, Discord)</li>
                <li>Existing crypto wallets</li>
                <li>Embedded wallets (created on login)</li>
              </ul>
              <div className="mt-6 bg-olas-light p-4 rounded-md">
                <h3 className="font-medium text-olas">Implementation Notes</h3>
                <p className="text-sm mt-2">
                  The Privy component creates an embedded wallet automatically for users who don't have one, 
                  making it accessible for both web2 and web3 users.
                </p>
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button className="bg-olas hover:bg-olas-dark">View Implementation</Button>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Live Demo</CardTitle>
            <CardDescription>
              Try the authentication flow
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="code" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="code">Code Example</TabsTrigger>
                <TabsTrigger value="demo">Live Demo</TabsTrigger>
              </TabsList>
              <TabsContent value="code" className="mt-4">
                <div className="bg-gray-100 p-4 rounded-md overflow-x-auto">
                  <pre className="text-xs">
                    {`// Initialize Privy component
const auth = create_privy_auth(
  privy_app_id=os.getenv("PRIVY_APP_ID"), 
  on_login=on_user_login
);

// Display the login UI with callback
auth_result = auth.login_ui(height=500);

// Handle auth result in callback
if (auth_result.authenticated && auth_result.continueToApp) {
  // Create user session
  // Redirect to app
}`}
                  </pre>
                </div>
              </TabsContent>
              <TabsContent value="demo" className="mt-4">
                <div className="bg-white border border-gray-200 rounded-md p-4">
                  <div className="text-center p-8">
                    <h3 className="text-lg font-medium mb-4">Connect to OLAS MCP</h3>
                    <Button className="bg-olas hover:bg-olas-dark w-full">
                      Connect with Privy
                    </Button>
                    <p className="mt-4 text-sm text-gray-500">
                      Connect with email, social accounts, or wallet
                    </p>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>

      <div className="mt-12">
        <Card>
          <CardHeader>
            <CardTitle>Implementation Steps</CardTitle>
            <CardDescription>
              How to integrate Privy authentication with your Streamlit app
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ol className="space-y-4 list-decimal pl-5">
              <li>
                <strong>Install dependencies</strong>
                <p className="text-sm mt-1">
                  Add Privy browser SDK to your Streamlit component
                </p>
              </li>
              <li>
                <strong>Create the Privy component</strong>
                <p className="text-sm mt-1">
                  Implement a custom component that wraps the Privy SDK
                </p>
              </li>
              <li>
                <strong>Handle authentication events</strong>
                <p className="text-sm mt-1">
                  Create callback functions for login/logout events
                </p>
              </li>
              <li>
                <strong>Update UI based on auth state</strong>
                <p className="text-sm mt-1">
                  Show different views for authenticated vs unauthenticated users
                </p>
              </li>
              <li>
                <strong>Create account management</strong>
                <p className="text-sm mt-1">
                  Link the wallet address to your app's account system
                </p>
              </li>
            </ol>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AuthDemo;