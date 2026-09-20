"""Market quote routes (stocks + crypto), backed by services/market.py."""
from flask import Blueprint, jsonify, request

from auth import require_auth
from services import market

market_bp = Blueprint('market', __name__)


@market_bp.route('/api/market', methods=['GET'])
@require_auth
def get_quotes():
    """Quotes for a comma-separated symbol list.

    Stocks resolve through Yahoo's chart endpoint; tickers in
    ``market.CRYPTO_IDS`` resolve through CoinGecko. Unknown or malformed
    symbols are skipped, never fatal.
    """
    symbols = market.parse_symbols(request.args.get('symbols') or '')
    if not symbols:
        return jsonify({'success': True, 'quotes': [], 'count': 0})

    quotes = market.fetch_quotes(symbols)
    return jsonify({
        'success': True,
        'quotes': [q.to_dict() for q in quotes],
        'count': len(quotes),
        'missing': [s for s in symbols if s not in {q.symbol for q in quotes}],
    })
