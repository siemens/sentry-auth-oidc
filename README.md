# OIDC Auth for Sentry (Shibboleth)


An SSO provider for Sentry which enables [OpenID Connect](https://openid.net/connect/) Apps authentication for Shibboleth. This is a fork of [siemens/sentry-auth-oidc](https://github.com/siemens/sentry-auth-oidc), which was also forked from [getsentry/sentry-auth-google](https://github.com/getsentry/sentry-auth-google).

## Why fork, instead of adapting `siemens/sentry-auth-oidc` or `getsentry/sentry-auth-google` to work with every OIDC?
The maintainers have different ideas. See:
- https://github.com/getsentry/sentry-auth-google/pull/29
- https://github.com/getsentry/sentry/issues/5650
- Also the fork of `siemens/sentry-auth-oidc` doesn't work very well with Shibboleth
    - The scope `openid` is always returned for unauthorized users, which aren't in the given example entitlement `sentry-users`.
    - For that reason the request after authorization is redirected to sentry instead of directly showing an 403 error page on the identity provider side. 


## Install
```bash
pip install sentry-auth-oidc-shib
```


## Setup steps for usage with Shibboleth
### Shibboleth
- Configure `metadata/oidc-client.json`
    ```json
    {
        "scope": "openid profile email",
        "redirect_uris": [ 
            "https://sentry.example.com/auth/sso/" 
        ],
        "sector_identifier_uri": "https://sentry.example.com",
        "client_id": "<client-id>",
        "subject_type": "pairwise",
        "client_secret": "<client-secret>",
        "response_types": [ 
            "code"
        ],
        "grant_types": [ 
            "authorization_code"
        ]
    }
    ```
- Configure `conf/intercept/context-check-intercept-config.xml`
    ```xml
    # Content of 
    <bean id="shibboleth.context-check.Condition" parent="shibboleth.Conditions.AND">
        <constructor-arg>
            <list>
                <bean class="net.shibboleth.idp.profile.logic.SimpleAttributePredicate" p:useUnfilteredAttributes="true">
                    <property name="attributeValueMap">
                        <map>
                            <entry key="oidcPermissions">
                                <list>
                                    <value>true</value>
                                </list>
                            </entry>
                        </map>
                    </property>
                </bean>
            </list>
        </constructor-arg>
    </bean>
    ```
- Configure `conf/attribute-resolver.xml`
    ```xml
    <AttributeDefinition xsi:type="ScriptedAttribute" id="oidcPermissions" dependencyOnly="false">
        <InputDataConnector ref="myLDAP" attributeNames="eduPersonEntitlement"/>
        <Script><![CDATA[
            logger = Java.type("org.slf4j.LoggerFactory").getLogger("edu.internet2.middleware.shibboleth.resolver.Script.eduPersonPrincipalNameSource");

            // Get attribute to add
            peerEntityId = profileContext.getSubcontext("net.shibboleth.idp.profile.context.RelyingPartyContext").getRelyingPartyId();

            if (peerEntityId.equals("sentry.example.com") 
                    && eduPersonEntitlement.getValues().contains("urn:mace:example.com:permission:shibboleth:sentry-users")){ 
                logger.info("User can successfully login to " + peerEntityId);
                oidcPermissions.getValues().add("true");
            }	
        ]]>
        </Script>
    </AttributeDefinition>
    ```
- Configure `conf/relying-party.xml`
    ```xml
    <bean parent="RelyingPartyByName" c:relyingPartyIds="sentry.example.com">
        <property name="profileConfigurations">
        <list>
            <bean parent="OIDC.SSO" p:postAuthenticationFlows="#{ {'context-check'} }"/>
            <ref bean="OIDC.UserInfo" />
        </list>
        </property>
    </bean>
    ```

### Sentry
- Configure `sentry/sentry.conf.py`
    ```python
    OIDC_CLIENT_ID = "<client-id>"
    OIDC_CLIENT_SECRET = "<client-secret>"
    OIDC_SCOPE = "openid profile email"
    OIDC_DOMAIN = "https://shibboleth.example.com"
    ```
- Configure `sentry/enhance-image.sh`
    ```bash
    pip install sentry-auth-oidc-shib
    ```