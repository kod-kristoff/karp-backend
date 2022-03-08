from fastapi import status

from karp import auth


class TestQuery:
    def test_route_exist(self, fa_data_client):
        response = fa_data_client.get('/query/places')
        print(f'{response.json()=}')
        assert response.status_code != status.HTTP_404_NOT_FOUND


def test_query_wo_q(
    fa_data_client,
    read_token: auth.AccessToken,
    app_context,
):
    response = fa_data_client.get(
        '/query/places',
        headers=read_token.as_header(),
        # stream=True,
    )

    assert response.status_code == status.HTTP_200_OK
    print(f'{response.text=}')
    print(f'{response.json()=}')
