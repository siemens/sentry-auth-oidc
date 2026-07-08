# Custom Provider Icon

Sentry does not provide a regular admin menu for adding custom CSS to the login page. For self-hosted Sentry, add the icon styling as part of your Sentry deployment.

The OIDC provider uses the stable provider key `oidc` for its logo CSS class. This means the selector remains `.provider-logo.oidc` even when `OIDC_PROVIDER_NAME` is set to a custom display name such as `"Acme Corp SSO"`.

## Bundled Icon

The recommended approach is to build a small custom Sentry image that ships the icon with Sentry's static files and appends the CSS to Sentry's frontend stylesheet.

```dockerfile
FROM getsentry/sentry:<version>

COPY your-oidc-icon.svg /usr/src/sentry/src/sentry/static/sentry/images/your-oidc-icon.svg

RUN cat >> /usr/src/sentry/src/sentry/static/sentry/dist/entrypoints/sentry.css <<'EOF'
.provider-logo.oidc {
  background-image: url("/_static/sentry/images/your-oidc-icon.svg");
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}
EOF
```

Use the same image for the Sentry web container so the login page can serve the updated stylesheet.

## External Icon URL

If the icon should be hosted outside the Sentry image, make sure the host is allowed by your deployment's `CSP_IMG_SRC` configuration.

```dockerfile
FROM getsentry/sentry:<version>

RUN cat >> /usr/src/sentry/src/sentry/static/sentry/dist/entrypoints/sentry.css <<'EOF'
.provider-logo.oidc {
  background-image: url("https://example.com/your-oidc-icon.svg");
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}
EOF
```

## Notes

- Keep the selector as `.provider-logo.oidc`; it is based on the provider key, not the display name.
- Prefer a bundled static asset when the deployment enforces a restrictive content security policy.
- Avoid reverse-proxy HTML or CSS injection unless you cannot build a custom image. It is more fragile than baking the CSS into the image.
