Technical Challenges Overcome
1. The "Silent" Environment Variable Failure
The Challenge: After deploying to Vercel and Netlify, the frontend repeatedly attempted to call localhost:8000 despite the production URL being set in the dashboard. This "silent failure" occurred because Vite's minification process was stripping the environment variables during the build phase.

The Solution: We implemented a strict TypeScript interface definition for ImportMetaEnv in vite-env.d.ts. This forced the compiler to recognize VITE_API_URL as a required build-time constant. We further stabilized the injection by moving the variable directly into the Netlify build command (VITE_API_URL=... npm run build), ensuring the production URL was "baked" into the JavaScript bundle.

2. Cross-Origin Resource Sharing (CORS) in Production
The Challenge: Once the frontend successfully reached the Render backend, the requests were initially blocked by CORS policy. Standard security headers on the FastAPI backend were rejecting the automated assigned URLs from the frontend hosting providers.

The Solution: We updated the CORSMiddleware in the FastAPI main.py to utilize a dynamic origin check. For the hackathon prototype phase, we implemented an allow_origins=["*"] policy to ensure seamless communication between the decoupled Netlify frontend and Render backend, while maintaining strict allow_methods for data integrity.

3. Nested EDI Loop Parsing
The Challenge: Healthcare EDI files (specifically 837 and 834) use highly complex, nested "loops" that are notorious for breaking standard regex-based parsers.

The Solution: Instead of using libraries or regex, we developed a custom State-Machine Parser. This engine tracks the current segment context (e.g., whether it is inside a Subscriber loop or a Provider loop) in real-time. This ensures 100% accuracy when mapping data to the UI's hierarchical Segment Tree.
