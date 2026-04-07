# OIDC Icon Example

This directory contains an example OIDC icon that can be used with your Sentry instance.

## Using the Icon

The `oidc-icon.svg` file is a simple icon representing authentication/identity with a user and lock symbol.

### Option 1: Host the icon file

1. Upload `oidc-icon.svg` to a publicly accessible location or your Sentry's static files directory
2. Add the following CSS to your Sentry instance's custom CSS:

```css
.provider-logo.oidc {
    background-image: url('/path/to/oidc-icon.svg');
}
```

### Option 2: Use inline SVG as data URI

You can also convert the SVG to a data URI and include it directly in the CSS.
To generate a base64-encoded data URI from the SVG file:

```bash
# On Linux/macOS
base64 -w 0 oidc-icon.svg

# Or use an online tool like https://yoksel.github.io/url-encoder/
```

Then use it in your CSS:

```css
.provider-logo.oidc {
    background-image: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy...');
}
```

### Option 3: Create your own icon

Feel free to create your own custom icon! The icon should:
- Be square (36x36 viewBox recommended for SVG)
- Work well at small sizes
- Match your organization's branding

Then follow the same steps above to add the custom CSS to your Sentry instance.

## Icon CSS Class

The CSS class for the provider logo is determined by the `OIDC_PROVIDER_NAME` setting:
- Default (`OIDC_PROVIDER_NAME = "OIDC"`): CSS class is `.provider-logo.oidc`
- Custom name (`OIDC_PROVIDER_NAME = "My Company SSO"`): CSS class is `.provider-logo.my-company-sso`

The provider name is converted to lowercase with spaces replaced by hyphens.
