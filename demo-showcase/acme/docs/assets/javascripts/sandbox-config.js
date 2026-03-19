/*
 * Sandbox endpoint configuration for Acme demo site.
 *
 * This file is loaded BEFORE acme-sandbox.js.
 * It reads the Postman mock server URLs and exposes them
 * as window.ACME_SANDBOX for all interactive testers.
 *
 * To change endpoints, edit mkdocs.yml extra.sandbox section.
 */
(function () {
  'use strict';

  // Postman Mock Server base URL for the Acme demo collection.
  // All protocol endpoints are routed through this single mock.
  var MOCK_BASE = 'https://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io';

  window.ACME_SANDBOX = {
    rest_base_url:      MOCK_BASE + '/v1',
    graphql_url:        MOCK_BASE + '/graphql',
    grpc_gateway_url:   MOCK_BASE + '/grpc/invoke',
    asyncapi_ws_url:    'wss://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io/ws',
    websocket_url:      'wss://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io/realtime'
  };
})();
