#!/usr/bin/env python3
"""
Smart Garden Application Entry Point

This script serves as the entry point for the Smart Garden application.
It initializes and runs the Flask application with the development server.

The application factory pattern is used to create the Flask application
instance, which allows for better flexibility and testing capabilities.
"""

from app import create_app, db

# Create the Flask application instance using the factory function
app = create_app()

if __name__ == '__main__':
    # Run the application only if this file is executed directly
    # Debug mode is enabled for development purposes
    # Warning: Debug mode should be disabled in production
    app.run(debug=True)
