/*
 * Sandbox endpoint configuration for Acme demo site.
 *
 * The __POSTMAN_API_KEY__ placeholder is replaced at build time
 * by the deploy workflow with the actual key from GitHub Secrets.
 */
(function () {
  'use strict';

  var MOCK_BASE = 'https://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io';

  window.ACME_SANDBOX = {
    postman_api_key:    '__POSTMAN_API_KEY__',
    rest_base_url:      MOCK_BASE + '/v1',
    graphql_url:        MOCK_BASE + '/graphql',
    grpc_gateway_url:   MOCK_BASE + '/grpc/invoke',
    asyncapi_ws_url:    'wss://socketsbay.com/wss/v2/1/demo/',
    websocket_url:      'wss://socketsbay.com/wss/v2/1/demo/'
  };
})();
