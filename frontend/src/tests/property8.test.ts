import { test, expect } from 'vitest';
import fc from 'fast-check';
import * as fs from 'fs';
import * as path from 'path';

// Helper to extract all font-size declarations from CSS/Vue files
function getFontSizeDeclarations(dir: string): string[] {
    let decls: string[] = [];
    const files = fs.readdirSync(dir);
    
    for (const file of files) {
        const fullPath = path.join(dir, file);
        const stat = fs.statSync(fullPath);
        
        if (stat.isDirectory()) {
            decls.push(...getFontSizeDeclarations(fullPath));
        } else if (file.endsWith('.css') || file.endsWith('.vue')) {
            const content = fs.readFileSync(fullPath, 'utf8');
            // Extract font-size: ...;
            const matches = content.match(/font-size:\s*([^;]+);/g);
            if (matches) {
                decls.push(...matches.map(m => m.trim()));
            }
        }
    }
    return decls;
}

test('Property 8: font sizes use clamp()', () => {
    const srcDir = path.resolve(__dirname, '..');
    const allDeclarations = getFontSizeDeclarations(srcDir);
    
    const relevantDecls = allDeclarations.filter(d => 
        !d.includes('inherit') && !d.includes('em;') && !d.includes('%') && !d.includes('var(')
    );

    expect(relevantDecls.length).toBeGreaterThan(0);

    fc.assert(
        fc.property(
            fc.constantFrom(...relevantDecls),
            (decl) => {
                return decl.includes('clamp(');
            }
        ),
        { numRuns: 100 }
    );
});
