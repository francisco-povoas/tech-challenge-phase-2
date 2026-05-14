# ADR 0001: Uso do PostgreSQL como banco de dados

## Status

Aceita

## Contexto

A aplicação precisa armazenar dados de lientes, veiculos, ordens de serviço, serviços, orçamento e pagamento.

Essas informações possuem relações importantes entre si. Uma ordem de serviço, por exemplo, está ligada a um cliente, veículo que por sua vez pertence a um cliente. serviços do catalogo, itens de estoque e orçamento.

## Decisão

Utilizar PostgreSQL como banco de dados principal da aplicação.

## Justificativa

O PostgreSQL foi escolhido por ser um banco relacional robusto, gratuito, amplamente utilizado no mercado, de conhecimento do desenvolvedor e adequado para dados estruturados.

Como o domínio da aplicação possui várias entidades relacionadas, o modelo relacional facilita a organização, a consistência e a consulta dos dados.

Além disso, o PostgreSQL possui boa integração com Python, SQLAlchemy/SQLModel e Alembic.


## Alternativas consideradas

O MongoDB também poderia ser usado, já que permite trabalhar com documentos de forma flexível. Porém, como a aplicação possui muitos dados relacionados e precisa manter consistência entre eles, um banco relacional se encaixa melhor neste momento.

O SQLite poderia ser útil para testes ou desenvolvimento local, mas não foi escolhido como banco principal por ser mais limitado para um ambiente de produção nas fases posteriores.

## Consequências

A aplicação terá um modelo de dados mais consistente e organizado.

As alterações no banco serão controladas por migrations através do alembic.

A estrutura das tabelas e relacionamentos precisará ser bem planejada.