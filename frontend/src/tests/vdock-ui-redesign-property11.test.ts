import { test, expect } from 'vitest';
import fc from 'fast-check';
import { readFileSync } from 'fs';
import { resolve } from 'path';

// Feature: vdock-ui-redesign, Property 11: New animation declarations use shared easing tokens
//
// For any CSS `transition` or `animation-timing-function` declaration introduced by this
// redesign's stylesheet changes, its timing value SHALL be one of `var(--ease-out)`,
// `var(--ease-spring)`, or `var(--ease-io)`, and SHALL NOT be a newly introduced literal
// `cubic-bezier(...)` value.
//
// Validates: Requirements 7.3
//
// This redesign has so far modified/introduced timing-function usage in two places:
//   - frontend/src/assets/styles/main.css   — defines the tokens themselves (source of
//     truth, not "usage" of a token, so the token definitions are exempt from this check).
//   - frontend/src/views/DashboardView.vue  — the `.page-slide-left` / `.page-slide-right`
//     enter/leave-active rules were retuned in task 1.2 to use `var(--ease-io)`.
//
// The test statically parses the `<style>` block of DashboardView.vue, extracts every
// `transition:` / `transition-timing-function:` / `animation-timing-function:` declaration
// belonging to the `.page-slide-*` rules touched by this feature, pulls out any explicit
// custom timing-function component (a `var(--ease-*)` token or a raw `cubic-bezier(...)`
// literal) from each comma-separated part, and asserts every such component is one of the
// three shared tokens rather than a newly introduced literal.

const SHARED_EASING_TOKENS = ['var(--ease-out)', 'var(--ease-spring)', 'var(--ease-io)'];

/**
 * Extracts the body of every CSS rule in `cssText` whose selector list contains at least
 * one selector matching `selectorPattern`.
 */
function extractRuleBodiesForSelector(cssText: string, selectorPattern: RegExp): string[] {
    const bodies: string[] = [];
    // Match "<selector list>{<body>}" blocks (non-greedy body, no nested braces expected
    // for these simple transition rules).
    const ruleRegex = /([^{}]+)\{([^{}]*)\}/g;
    let match: RegExpExecArray | null;
    while ((match = ruleRegex.exec(cssText)) !== null) {
        const selectorList = match[1];
        const body = match[2];
        if (selectorPattern.test(selectorList)) {
            bodies.push(body);
        }
    }
    return bodies;
}

/**
 * Extracts every `transition:` / `transition-timing-function:` / `animation-timing-function:`
 * declaration value from a CSS rule body.
 */
function extractTimingDeclarations(ruleBody: string): string[] {
    const declRegex = /(transition|transition-timing-function|animation-timing-function)\s*:\s*([^;]+);/g;
    const values: string[] = [];
    let match: RegExpExecArray | null;
    while ((match = declRegex.exec(ruleBody)) !== null) {
        values.push(match[2].trim());
    }
    return values;
}

/**
 * Splits a (possibly multi-transition) declaration value on top-level commas — i.e. commas
 * that are not nested inside parentheses (so `cubic-bezier(0.4, 0, 0.2, 1)` stays intact).
 */
function splitTopLevelCommas(value: string): string[] {
    const parts: string[] = [];
    let depth = 0;
    let current = '';
    for (const char of value) {
        if (char === '(') depth++;
        if (char === ')') depth--;
        if (char === ',' && depth === 0) {
            parts.push(current.trim());
            current = '';
        } else {
            current += char;
        }
    }
    if (current.trim().length > 0) parts.push(current.trim());
    return parts;
}

/**
 * Pulls the explicit custom timing-function component out of a single transition part, if
 * present. Returns either a `var(--ease-*)` token string, a raw `cubic-bezier(...)` literal
 * string, or `null` when the part has no explicit custom timing function (e.g. it only uses
 * a standard keyword like `ease` or `linear`, which this property does not constrain).
 */
function extractTimingFunctionComponent(transitionPart: string): string | null {
    const cubicBezierMatch = transitionPart.match(/cubic-bezier\([^)]*\)/);
    if (cubicBezierMatch) return cubicBezierMatch[0];

    const varEaseMatch = transitionPart.match(/var\(--ease-[a-z]+\)/);
    if (varEaseMatch) return varEaseMatch[0];

    return null;
}

const dashboardViewPath = resolve(__dirname, '../views/DashboardView.vue');
const dashboardViewContent = readFileSync(dashboardViewPath, 'utf-8');

// Isolate the <style> block so we only ever look at CSS, never script/template text.
const styleBlockMatch = dashboardViewContent.match(/<style[^>]*>([\s\S]*?)<\/style>/);
const styleBlock = styleBlockMatch ? styleBlockMatch[1] : '';

// The `.page-slide-*` rules are the only timing-function declarations this feature has
// introduced/modified in DashboardView.vue so far (task 1.2).
const pageSlideRuleBodies = extractRuleBodiesForSelector(styleBlock, /\.page-slide-(left|right)-(enter|leave)-active/);

const timingDeclarations = pageSlideRuleBodies.flatMap(extractTimingDeclarations);

const timingFunctionComponents = timingDeclarations
    .flatMap(splitTopLevelCommas)
    .map(extractTimingFunctionComponent)
    .filter((component): component is string => component !== null);

test('Feature: vdock-ui-redesign, Property 11: New animation declarations use shared easing tokens', () => {
    // Guard against a vacuous property: the page-slide rules must actually declare at
    // least one explicit custom timing function for this test to be meaningful.
    expect(timingFunctionComponents.length).toBeGreaterThan(0);

    fc.assert(
        fc.property(
            fc.constantFrom(...timingFunctionComponents),
            (component) => {
                // Must not be a newly introduced literal cubic-bezier(...) value.
                expect(component.startsWith('cubic-bezier(')).toBe(false);
                // Must be exactly one of the three shared easing tokens.
                expect(SHARED_EASING_TOKENS).toContain(component);
            }
        ),
        { numRuns: 100 }
    );
});
