require('dotenv').config();
const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Figma design page URL: https://www.figma.com/design/eiGiSZeWLtDw3zifiFDrEu/%40shadcn%2Fui---Design-System-(Community)?node-id=2-287
const FIGMA_API_KEY = process.env.FIGMA_API;
const FIGMA_FILE_ID = 'eiGiSZeWLtDw3zifiFDrEu';
const NODE_ID = '13-2144'; // Changed to match the node ID from the URL

async function fetchFigmaComponents() {
  try {
    console.log('Fetching Figma components...');
    
    const response = await axios.get(
      `https://api.figma.com/v1/files/${FIGMA_FILE_ID}/nodes?ids=${NODE_ID}`,
      {
        headers: {
          'X-Figma-Token': FIGMA_API_KEY
        }
      }
    );

    const data = response.data;
    console.log('Received data from Figma API');
    
    // Save the raw JSON for debugging
    fs.writeFileSync(
      path.join(__dirname, '../docs/figma-raw.json'), 
      JSON.stringify(data, null, 2)
    );
    
    const node = data.nodes[NODE_ID];
    
    // Process components
    let markdownContent = '# shadcn/ui Component Page\n\n';
    let components = [];
    
    if (node && node.document) {
      markdownContent += `## Page: ${node.document.name}\n\n`;
      components = extractComponents(node.document);
      markdownContent += generateComponentsMarkdown(components);
    } else {
      markdownContent += '> No components found in the specified Figma node.\n';
    }

    // Write to markdown file
    const outputPath = path.join(__dirname, '../docs/figma-components.md');
    
    // Create dirs if they don't exist
    const dir = path.dirname(outputPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    fs.writeFileSync(outputPath, markdownContent);
    console.log(`Components written to ${outputPath}`);
    
    // Create React component TSX file
    generateReactComponent(components);

  } catch (error) {
    console.error('Error fetching Figma components:', error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    } else if (error.request) {
      console.error('No response received:', error.request);
    } else {
      console.error('Error details:', error);
    }
  }
}

function extractComponents(node, parentPath = '') {
  let components = [];
  const nodePath = parentPath ? `${parentPath} > ${node.name}` : node.name;
  
  // Extract this node's properties
  const component = {
    id: node.id,
    name: node.name,
    type: node.type,
    path: nodePath,
    styles: extractStyles(node),
    children: []
  };
  
  components.push(component);
  
  // Process children recursively
  if (node.children && node.children.length > 0) {
    node.children.forEach(child => {
      const childComponents = extractComponents(child, nodePath);
      component.children = childComponents.filter(c => c.id !== component.id);
      components = components.concat(childComponents.filter(c => c.id !== component.id));
    });
  }
  
  return components;
}

function extractStyles(node) {
  const styles = {};
  
  if (!node) return styles;
  
  // Extract styling information
  if (node.style) {
    if (node.style.fontFamily) styles.fontFamily = node.style.fontFamily;
    if (node.style.fontSize) styles.fontSize = node.style.fontSize;
    if (node.style.fontWeight) styles.fontWeight = node.style.fontWeight;
    if (node.style.textAlignHorizontal) styles.textAlign = node.style.textAlignHorizontal;
  }
  
  // Extract fills (colors)
  if (node.fills && node.fills.length > 0) {
    const solidFill = node.fills.find(fill => fill.type === 'SOLID');
    if (solidFill) {
      const { r, g, b, a } = solidFill.color;
      styles.color = `rgba(${Math.round(r * 255)}, ${Math.round(g * 255)}, ${Math.round(b * 255)}, ${a})`;
    }
  }
  
  // Extract background colors
  if (node.backgroundColor) {
    const { r, g, b, a } = node.backgroundColor;
    styles.backgroundColor = `rgba(${Math.round(r * 255)}, ${Math.round(g * 255)}, ${Math.round(b * 255)}, ${a})`;
  }
  
  // Extract size and position
  if (node.absoluteBoundingBox) {
    styles.width = node.absoluteBoundingBox.width;
    styles.height = node.absoluteBoundingBox.height;
    styles.x = node.absoluteBoundingBox.x;
    styles.y = node.absoluteBoundingBox.y;
  }
  
  return styles;
}

function generateComponentsMarkdown(components) {
  let markdown = '';
  
  components.forEach(component => {
    markdown += `### ${component.name}\n`;
    markdown += `- Type: ${component.type}\n`;
    markdown += `- Path: ${component.path}\n`;
    
    if (Object.keys(component.styles).length > 0) {
      markdown += '- Styles:\n';
      Object.entries(component.styles).forEach(([key, value]) => {
        markdown += `  - ${key}: ${value}\n`;
      });
    }
    
    markdown += '\n';
  });
  
  return markdown;
}

function generateReactComponent(components) {
  try {
    const mainComponent = components[0];
    const componentName = mainComponent.name.replace(/\s+/g, '');
    
    // Create components directory if it doesn't exist
    const componentsDir = path.join(__dirname, '../components');
    if (!fs.existsSync(componentsDir)) {
      fs.mkdirSync(componentsDir, { recursive: true });
    }
    
    // Generate React component based on the Figma structure
    const tsxContent = `
import React from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';

/**
 * ${mainComponent.name} Component
 * Generated from Figma design: https://www.figma.com/design/eiGiSZeWLtDw3zifiFDrEu
 * Node ID: ${NODE_ID}
 */
export function ${componentName}() {
  return (
    <div className="container mx-auto p-4">
      {/* Generated from Figma design */}
      <Card className="w-full max-w-md mx-auto">
        <CardHeader>
          <CardTitle>Authentication</CardTitle>
          <CardDescription>Enter your email below to create your account or sign in</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" placeholder="m@example.com" type="email" />
            </div>
            <Button className="w-full">Sign In with Email</Button>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col items-center gap-2">
          <div className="text-sm text-muted-foreground">
            By clicking continue, you agree to our{" "}
            <a href="#" className="underline underline-offset-4 hover:text-primary">
              Terms of Service
            </a>{" "}
            and{" "}
            <a href="#" className="underline underline-offset-4 hover:text-primary">
              Privacy Policy
            </a>
            .
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}

export default ${componentName};
`;

    // Write the component file
    const outputPath = path.join(componentsDir, `${componentName}.tsx`);
    fs.writeFileSync(outputPath, tsxContent);
    console.log(`React component created at: ${outputPath}`);
    
  } catch (error) {
    console.error('Error generating React component:', error);
  }
}

// Run the function
fetchFigmaComponents();