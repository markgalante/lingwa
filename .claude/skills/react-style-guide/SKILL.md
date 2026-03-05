---
name: react-style-guide
description: React component development style guidelines. Use this skill whenever creating React components, functional components, or any React code. Ensures consistent code style including component syntax, import patterns, and formatting across the project.
---

# React Style Guide

Style guidelines for React component development.

## Component Definitions

**Prefer function declarations over arrow functions:**

```javascript
// ✓ Good
function MyComponent() {
  return <div>Hello</div>;
}

// ✗ Avoid
const MyComponent = () => {
  return <div>Hello</div>;
};
```

Use standard function declaration syntax for all React components. This provides better readability and aligns with our project conventions.

## Import Patterns

**Always import React using namespace syntax:**

```javascript
// ✓ Good
import * as React from 'react';

function MyComponent() {
  const [count, setCount] = React.useState(0);
  // ...
}

// ✗ Avoid
import React from 'react';
import { useState } from 'react';
```

Use `import * as React from 'react'` for all React imports, then access hooks and utilities via the `React` namespace.

## Additional Guidelines

[Add more style guidelines here as the project develops]

## Common Patterns

[Document common patterns and best practices as they emerge]

## FAQ

[Add frequently asked questions and their answers]